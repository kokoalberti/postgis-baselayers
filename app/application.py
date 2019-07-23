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

# Version
__version__ = '0.1.0'

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

app.config.from_object('settings')

# Create the instance directory
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Create some common exceptions for things that can go wrong
class DatabaseException(Exception):
    pass

class PostgisMissingException(Exception):
    pass

class ConfigError(Exception):
    pass

class ApplicationError(Exception):
    pass

class InstallTerminated(Exception):
    pass

class InstallFailed(Exception):
    pass

class ApplicationNotInitialized(Exception):
    pass

# Create our SqliteHuey instance in Flask's instance_path directory
huey_file = os.path.join(app.instance_path, 'huey.db')
def get_huey(reset=False):
    if reset:
        os.remove(huey_file)
    return SqliteHuey(filename=huey_file)
huey = get_huey()

# Function to fetch a database connection
def get_db():
    conn = psycopg2.connect(dbname=app.config.get("POSTGRES_DB",""),
                    user=app.config.get("POSTGRES_USER",""), 
                    password=app.config.get("POSTGRES_PASSWORD",""),
                    port=app.config.get("POSTGRES_PORT", 5432),
                    host=app.config.get("POSTGRES_HOST",""))
    return conn

# Validate the environment to make sure several environment variables are 
# defined, and it sets up the database connectivity on flask's g.conn.
@app.before_request
def connect_db():
    # Create the database connection on g.conn
    if not hasattr(g, 'conn'):
        g.conn = get_db()

    # Don't do these checks when our endpoint is 'try_install_postgis'...
    if request.endpoint != 'try_install_postgis':

        # Verify PostGIS is installed
        cur = g.conn.cursor()
        try:
            cur.execute("SELECT PostGIS_Lib_Version();")
            g.postgis_version = cur.fetchone()[0]
        except psycopg2.errors.UndefinedFunction as e:
            raise PostgisMissingException("{}\n------------\nIt looks like PostGIS is not installed in this database?\n\nYou can install it manually by running this SQL command on the database: \n\nCREATE EXTENSION postgis;\n\nOr postgis-baselayers can try to do it automatically if you click the button below...\n".format(e))

        # Verify that our own schema exists, otherwise raise ApplicationNotInitialized,
        # which will show the initialization screen.
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = 'postgis_baselayers');")
        res = cur.fetchone()[0]
        if not res:
            raise ApplicationNotInitialized("PostGIS Baselayers is not initialized yet on this database.")

# When the app context is destroyed, close the database connection.
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'conn'):
        g.conn.close()

# Context processor to inject some common data into templates
@app.context_processor
def template_variables():
    return dict(pg_baselayers_version=__version__)

# Handle any errors using an error page
@app.errorhandler(DatabaseException)
@app.errorhandler(PostgisMissingException)
@app.errorhandler(ConfigError)
@app.errorhandler(ApplicationError)
@app.errorhandler(psycopg2.OperationalError)
def handle_error(error):
    print(type(error))
    error_type = type(error).__name__
    return render_template("error.html", **locals())

@app.errorhandler(ApplicationNotInitialized)
@app.route('/initialize', methods=['GET','POST'])
def initialization_error(error=""):
    """
    Show template to initialize the database.
    """
    if request.method == 'GET':
        return render_template('initialize.html')

    if request.method == 'POST' and request.form.get("initialize") == 'yes':
        cur = g.conn.cursor()
        #TODO: put this in a separate 'create_schema.sql' file and run that
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
        return redirect(url_for('index'))
    else:
        abort(404)

@app.route('/reset')
def reset():
    huey = get_huey(reset=True)
    return "Reset huey"

@app.route('/')
def index():
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

@app.route("/try-postgis-install", methods=["POST"])
def try_install_postgis():
    """
    Tries to create the postgis extention.
    """
    cur = g.conn.cursor()
    cur.execute("CREATE EXTENSION postgis;")
    g.conn.commit()
    return redirect(url_for('index'))

@app.route("/install", methods=['POST'])
def install():
    """
    TODO: Validate input before passing to queue, and return/flash error 
          otherwise.
    """
    cur = g.conn.cursor()
    # Valid targets are:
    valid_targets = ('install', 'uninstall')

    # Make a list of valid keys
    cur.execute("SELECT key FROM postgis_baselayers.layer")
    valid_keys = [_[0] for _ in cur.fetchall()]

    for key, target in request.form.items():

        if target not in valid_targets:
            raise ApplicationError(f"Request contains invalid target: '{target}'")

        if key not in valid_keys:
            raise ApplicationError(f"Request contains invalid key: '{key}'")

        try:
            task = run_task(key, target)
            cur.execute("UPDATE postgis_baselayers.layer SET status=2 WHERE key=%s;", (key, ))
            g.conn.commit()
        except:
            g.conn.rollback()
            raise ApplicationError("Unexpected error while creating task.")

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
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            layer.key as key,
            layer.dataset_name as dataset, 
            layer.name as layer
        FROM 
            postgis_baselayers.layer 
        ORDER BY 
            layer.key
    """)
    layers = cur.fetchall()

    cur.execute("SELECT PostGIS_Full_Version() AS postgis_version, version() as postgresql_version;")
    version_info = cur.fetchone()
    return render_template("settings.html", **locals())


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

            # Run make
            makefile = os.path.join(temp_dir.name, f"{layer}.make")
            cmd = ["/usr/bin/make", "-f", makefile, target]
            logger.info(f"Running subprocess '{cmd}'")

            # Craft some environment variables to help the subprocess. These 
            # should be defined already when using a Docker environment, but 
            # lets not assume that and just inherit them from the application
            # config, which will in turn get them from the environment if they
            # are defined there.
            subprocess_env = {
                'POSTGRES_HOST': app.config.get('POSTGRES_HOST'),
                'POSTGRES_PORT': app.config.get('POSTGRES_PORT'),
                'POSTGRES_DB': app.config.get('POSTGRES_DB'),
                'POSTGRES_USER': app.config.get('POSTGRES_USER'),
                'POSTGRES_PASSWORD': app.config.get('POSTGRES_PASSWORD'),
                'POSTGRES_URI': app.config.get('POSTGRES_URI'),
                'POSTGRES_OGR': app.config.get('POSTGRES_OGR')
            }

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
                        info = (info[:500] + '(...)') if len(info) > 500 else info
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
            log_content = logstream.getvalue()

            # Remove passwords from logfile
            postgres_uri_safe = "postgresql://{POSTGRES_USER}:XXXXXX@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}".format(**os.environ)
            log_content = log_content.replace(os.environ.get("POSTGRES_URI"), postgres_uri_safe)

            postgres_ogr_safe = 'PG:"dbname={POSTGRES_DB} host={POSTGRES_HOST} port={POSTGRES_PORT} user={POSTGRES_USER} password=XXXXXX"'.format(**os.environ)
            log_content = log_content.replace(os.environ.get("POSTGRES_OGR"), postgres_ogr_safe)

            cur.execute("""
                INSERT INTO 
                    postgis_baselayers.log 
                    (layer_key, task_id, target, info, log) 
                VALUES 
                    (%s, %s, %s, %s, %s)
            """, (task.args[0], task.id, target, message, log_content))
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

    if task_value is None:
        logger.info("Task completed but did not return a value. Settings task status to error.")
        task_value = 4
        
    cur.execute("UPDATE postgis_baselayers.layer SET status=%s, info='' WHERE key=%s;", (task_value, task.args[0]))
    conn.commit()
    conn.close()
    logger.info("Done.")
