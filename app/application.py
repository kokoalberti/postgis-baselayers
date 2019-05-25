import sys
import os
import logging
import json
import shutil
import psycopg2
import time
import subprocess
import copy
import markdown
import tempfile

from threading import Timer
from glob import glob
from functools import wraps
from io import StringIO, BytesIO


from psycopg2.extras import DictCursor, RealDictCursor
from dotenv import load_dotenv
from huey import SqliteHuey

from flask import Flask, render_template, redirect, url_for, g, request, \
                  jsonify, Markup
from flask.json import dumps

# Set up logging to mirror any messages to stdout
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Load the dotenv files in the path
load_dotenv()

# Create the application object and configure it
app = Flask(__name__)

###
### Do some set up of the Huey task queue and the database connectivity 
### require by the application.
###

class DatabaseException(Exception):
    pass

class ConfigError(Exception):
    pass

class ApplicationError(Exception):
    pass

class InstallTerminated(Exception):
    pass

class InstallFailed(Exception):
    pass

if 'POSTGIS_BASELAYERS_WORKDIR' not in os.environ:
    os.environ['POSTGIS_BASELAYERS_WORKDIR'] = '/opt/postgis-baselayers'

# Create our SqliteHuey instance
huey_file = os.path.join(os.environ['POSTGIS_BASELAYERS_WORKDIR'], 'huey.db')
def get_huey(reset=False):
    if reset:
        os.remove(huey_file)
    return SqliteHuey(filename=huey_file)

huey = get_huey()

# Function to fetch a database connection
def get_db():
    conn = psycopg2.connect(dbname=os.environ.get("POSTGRES_DB",""),
                    user=os.environ.get("POSTGRES_USER",""), 
                    password=os.environ.get("POSTGRES_PASSWORD",""),
                    port=os.environ.get("POSTGRES_PORT", 5432),
                    host=os.environ.get("POSTGRES_HOST",""))
    return conn

# Validate the environment to make sure several environment variables are 
# defined, and it sets up the database connectivity on flask's g.conn.
@app.before_request
def validate_environment():
    #Check that our workdir is set
    if 'POSTGIS_BASELAYERS_WORKDIR' not in os.environ:
        raise ConfigError('POSTGIS_BASELAYERS_WORKDIR environment variable not '
                          'set.')

    #Check that workdir exists
    if not os.path.isdir(os.environ['POSTGIS_BASELAYERS_WORKDIR']):
        raise ConfigError('POSTGIS_BASELAYERS_WORKDIR is not a directory.')

    #Check that our huey database exists
    if not os.path.exists(huey_file):
        raise ConfigError('Huey SQLite database does not exist.')
    
    # Create the database connection on g.conn
    if not hasattr(g, 'conn'):
        try:
            g.conn = get_db()
        except psycopg2.OperationalError as e:
            raise DatabaseException("Database connection failed: {}".format(e))

# When the app context is destroyed, close the database connection.
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'conn'):
        g.conn.close()

# Handle any errors using an error page
@app.errorhandler(DatabaseException)
@app.errorhandler(ConfigError)
@app.errorhandler(ApplicationError)
@app.errorhandler(psycopg2.OperationalError)
def handle_error(error):
    return render_template("error.html", **locals())

# Update/install the database
@app.route('/update')
def update():
    """
    Creates or updates the metadata in the postgis_baselayers table. This table
    is used internally to keep track of which datasets have been installed and
    what their status is.
    """
    cur = g.conn.cursor()
    cur.execute("""
        CREATE SCHEMA IF NOT EXISTS postgis_baselayers;
        CREATE TABLE IF NOT EXISTS postgis_baselayers.dataset (
          name varchar(256) PRIMARY KEY,    -- eg. 'example'
          metadata json NOT NULL            -- flexible column for later use
        );
        CREATE TABLE IF NOT EXISTS postgis_baselayers.layer (
          key varchar(512) PRIMARY KEY,     -- eg. 'example.airports'
          name varchar(256) NOT NULL,       -- eg. 'airports'
          dataset_name varchar(256) REFERENCES postgis_baselayers.dataset(name),
          status int DEFAULT 0 NOT NULL,    -- 0: not installed; 1: installed; 2: queued; 3: working 4: error
          info varchar(512) DEFAULT '',     -- additional status info 
          metadata json NOT NULL            -- flexible column for later use
        );
        CREATE TABLE IF NOT EXISTS postgis_baselayers.log (
          id SERIAL PRIMARY KEY,
          created TIMESTAMP DEFAULT NOW(), 
          layer_key varchar(128) REFERENCES postgis_baselayers.layer(key),
          task_id varchar(128) NOT NULL, 
          target varchar(128) NOT NULL,     -- eg: 'install' or 'uninstall'
          info varchar(512),                -- additional status info
          log TEXT
        );
    """)
    g.conn.commit()

    # Parse and update all the datasets.
    metadata_path = os.path.join(app.root_path, "datasets", "*", "metadata.json")
    for metadata_file in glob(metadata_path):
        with open(metadata_file) as f:
            dataset = json.load(f)
            cur.execute("""
                INSERT INTO postgis_baselayers.dataset (name, metadata) 
                VALUES (%s, %s) 
                ON CONFLICT ON CONSTRAINT dataset_pkey 
                DO UPDATE SET metadata = %s;
            """, (dataset['name'], json.dumps(dataset['metadata']), json.dumps(dataset['metadata'])))

            for layer in dataset['layers']:
                key = "{}.{}".format(dataset['name'], layer['name'])
                cur.execute("""
                    INSERT INTO postgis_baselayers.layer (key, name, dataset_name, metadata)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT layer_pkey 
                    DO UPDATE SET metadata = %s;
                """, (key, layer['name'], dataset['name'], json.dumps(layer['metadata']), json.dumps(layer['metadata'])))
            g.conn.commit()
        #message = "Update failed"
        #return render_template('update.html', **locals())
    message = "Update/initialization completed."
    return render_template('update.html', **locals())

@app.route('/reset')
def reset():
    huey = get_huey(reset=True)
    return "Reset huey"

@app.route('/')
def index():
    cur = g.conn.cursor()

    # Check if the 'postgis_baselayers' schema exists. This is where we store 
    # status information for the application. If it doesn't exist (for example
    # when the app is accessed for the first time) then redirect to the 
    # 'update' view, where this schema and tables will be updates/initialized
    # automatically for the first time. The update view then redirects back
    # to the index page.
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = 'postgis_baselayers');")
    res = cur.fetchone()
    if not res[0]:
        return redirect(url_for('update'))

    # Fetch the metadata
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            layer.key,
            layer.dataset_name as dataset, 
            layer.name as layer,
            layer.info as info,
            layer.status,
            layer.metadata as layer_metadata,
            dataset.metadata as dataset_metadata
        FROM 
            postgis_baselayers.layer 
        LEFT JOIN 
            postgis_baselayers.dataset 
        ON 
            layer.dataset_name=dataset.name
        ORDER BY
            layer.key;
    """)
    layers = cur.fetchall()

    # Fetch processing/waiting info
    cur = g.conn.cursor()
    cur.execute("SELECT key FROM postgis_baselayers.layer WHERE status=3")
    layers_working = [_[0] for _ in cur.fetchall()]
    cur.execute("SELECT key FROM postgis_baselayers.layer WHERE status=2")
    layers_waiting = [_[0] for _ in cur.fetchall()]
    return render_template("index.html", **locals())

@app.route("/install", methods=['POST'])
def install():
    """
    TODO: Validate input before passing to queue, and return/flash error 
          otherwise.
    """
    cur = g.conn.cursor()
    valid_targets = ('install', 'uninstall')
    for key, target in request.form.items():
        if target in valid_targets:
            try:
                task = run_task(key, target)
                cur.execute("UPDATE postgis_baselayers.layer SET status=2 WHERE key=%s;", (key, ))
                g.conn.commit()
            except:
                g.conn.rollback()
                raise ApplicationError("Unexpected error while creating task.")
        else:
            raise ApplicationError("Request contains invalid target.")
    return redirect(url_for('index'))

@app.route("/logs/")
@app.route("/logs/<task_id>/")
def logs(task_id=None):
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    logs = None
    if not task_id:
        cur.execute("""
            SELECT 
                created, info, task_id
            FROM 
                postgis_baselayers.log
            ORDER BY 
                created DESC;
        """)
        logs = cur.fetchall()
    else:
        cur.execute("""
            SELECT 
                created, info, task_id, log
            FROM 
                postgis_baselayers.log
            WHERE 
                task_id=%s;
        """, (task_id,))
        logs = cur.fetchall()
    return render_template("logs.html", **locals())


@app.route("/settings/")
def settings():
    return render_template("settings.html")

@app.route("/dataset/<dataset_name>/")
def dataset(dataset_name):
    """
    Show dataset status information
    """
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            layer.key,
            layer.dataset_name as dataset, 
            layer.name as layer,
            layer.info as info,
            layer.status,
            layer.metadata as layer_metadata,
            dataset.metadata as dataset_metadata
        FROM 
            postgis_baselayers.layer 
        LEFT JOIN 
            postgis_baselayers.dataset 
        ON 
            layer.dataset_name=dataset.name
        WHERE 
            layer.dataset_name=%s 
    """, (dataset_name,))
    layers = cur.fetchall()

    base_dir = os.path.join(app.root_path, "datasets", dataset_name)

    with open(os.path.join(base_dir, "README.md")) as f:
        readme = Markup(markdown.markdown(f.read()))

    with open(os.path.join(base_dir, "metadata.json")) as f:
        dataset = json.load(f)

    return render_template("dataset.html", **locals())

@huey.task(context=True)
def run_task(key, target, task=None, timeout=1800):
    """
    Run a task

    TODO: Validate key and target
    """
    (dataset, layer) = key.split(".")
    status = None
    message = ''

    # Lock the task based on the dataset name. That way no more than one 
    # task can be run for any dataset (like installing and uninstalling it at 
    # the same time, or running two installs simultaneously)
    with huey.lock_task(key):

        logger = logging.getLogger("task_logger")
        logger.setLevel(logging.DEBUG)
        logstream = StringIO()
        streamhandler = logging.StreamHandler(logstream)
        logger.addHandler(streamhandler)

        conn = get_db()
        cur = conn.cursor()
        
        # TODO IMPORTANT!: Validate schema name as it's not escaped here.
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {dataset};")
        conn.commit()

        try:
            temp_dir = tempfile.TemporaryDirectory(prefix='pg-baselayers-task-')
            logger.info(f"Running task in temporary directory: {temp_dir.name}")

            # Copy the relevant files from the application's dataset directory.
            root_dir = os.path.join(app.root_path, 'datasets', dataset)
            logger.info("Dataset source dir is {}".format(root_dir))
            for f in os.listdir(root_dir):
                file_path = os.path.join(root_dir,f)
                if os.path.isfile(file_path):
                    shutil.copy2(file_path, temp_dir.name)
                    logger.info("Copied {} to {}".format(file_path, os.path.join(temp_dir.name, f)))

            # Determine makefile to use
            makefile = os.path.join(temp_dir.name, f"{layer}.make")
            if not os.path.exists(makefile):
                raise Exception(f"Makefile '{makefile}' not found.")

            # Set some additional environment variables for our installation
            # subprocesses.
            subprocess_env = copy.deepcopy(os.environ)
            #subprocess_env['PGOPTIONS'] = "-c search_path={},public".format(key)
            subprocess_env['POSTGRES_URI'] = "postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}".format(**os.environ)
            subprocess_env['POSTGRES_OGR'] = 'PG:"dbname={POSTGRES_DB} host={POSTGRES_HOST} port={POSTGRES_PORT} user={POSTGRES_USER} password={POSTGRES_PASSWORD}"'.format(**os.environ)

            # Run make
            cmd = ["/usr/bin/make", "-f", makefile, target]
            logger.info(f"Running subprocess '{cmd}'")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE, 
                                            env=subprocess_env, 
                                            cwd=temp_dir.name, 
                                            shell=False, 
                                            universal_newlines=True)

            #TODO: The process.kill() can still take a while to complete. Maybe
            #      start two timers, one for kill after timeout seconds, and 
            #      one using a more rigorous approach if that's possible.
            def process_terminator():
                logger.error("Timer expired, killing process... (This may also take a while to complete)")
                process.kill()

            
            timer = Timer(timeout, process_terminator)

            logger.info(f"Starting {timeout}s timer within which the installation process needs to finish.")
            timer.start()
            for line in iter(process.stdout.readline, b''):
                if line:
                    logger.info(line)
                    if line.startswith("STATUS="):
                        (_, info) = line.split("=", maxsplit=1)
                        cur.execute("""
                            UPDATE 
                                postgis_baselayers.layer 
                            SET info=%s 
                            WHERE key=%s;
                        """, (info, key))
                        conn.commit()
                else:
                    break

            print("Subprocess finished, wait for returncode...")
            process.wait()
            print("Returncode is {}".format(process.returncode))

            #TODO: Do we need a wait() and communicate() here or does 
            #      communicate() imply wait()ing?      
            stdout, stderr = process.communicate()

            if process.returncode < 0:
                raise InstallTerminated(stderr)

            if process.returncode != 0:
                raise InstallFailed(stderr)

            if process.returncode == 0:
                message = f"Completed {target} task on {key}."
                logger.info(message)
                if target == 'install':
                    status = 1
                if target == 'uninstall':
                    status = 0
            
        except InstallFailed as e:
            logger.error("ERROR! The installation failed with a non-zero returncode. More info: {}".format(e))
            message = f"Failed {target} on {key}. (An error occurred)"
            status = 4

        except InstallTerminated as e:
            logger.error("ERROR! The installation was terminated, most likely because it timed out. More info: {}".format(e))
            message = f"Failed {target} on {key}. (Process was terminated)"
            status = 4

        except Exception as e:
            logger.error("ERROR! The installation failed for an unknown reason. More info: {}".format(e))
            message = f"Failed {target} on {key}. (Unknown reason)"
            status = 4

        finally:
            # Destroy the temporary directory
            logger.info("Cleaning temporary directory...")
            temp_dir.cleanup()

            # Cancel any timer
            logger.info("Cancelling timer...")
            timer.cancel()

            # No matter what happens, flush the log and save in log table.
            logger.info("Flushing and saving logs...")
            streamhandler.flush()
            cur.execute("""
                INSERT INTO 
                    postgis_baselayers.log 
                    (layer_key, task_id, target, info, log) 
                VALUES 
                    (%s, %s, %s, %s, %s)
            """, (task.args[0], task.id, target, message, logstream.getvalue()))
            conn.commit()
            conn.close()

            # Return the status code of the task
            return status

@huey.pre_execute()
def pre_exec_hook(task):
    """
    Set dataset status to '3: working' before executing task.
    """
    logger.info("Pre-exec hook. Setting status to 3.")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE postgis_baselayers.layer SET status=3, info='' WHERE key=%s;", (task.args[0],))
    conn.commit()
    conn.close()
    logger.info("Done.")

@huey.post_execute()
def post_exec_hook(task, task_value, exc):
    """
    After executing task, set the dataset status to the status code returned 
    by the task.
    """
    logger.info(f"Post-exec hook. Setting status to {task_value}.")
    logger.info(f"Post-exec hook exception: {exc}")
    conn = get_db()
    cur = conn.cursor()
    if exc:
        logger.info("Exception found. Setting task status to error.")
        task_value = 4
    cur.execute("UPDATE postgis_baselayers.layer SET status=%s, info='' WHERE key=%s;", (task_value, task.args[0]))
    conn.commit()
    conn.close()
    logger.info("Done.")
