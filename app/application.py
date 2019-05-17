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

if 'POSTGIS_BASELAYERS_WORKDIR' not in os.environ:
    os.environ['POSTGIS_BASELAYERS_WORKDIR'] = '/opt/postgis-baselayers'

# Create our SqliteHuey instance
huey_file = os.path.join(os.environ['POSTGIS_BASELAYERS_WORKDIR'], 'huey.db')
huey = SqliteHuey(filename=huey_file)

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

    Status:
    0: unknown
    1: created/disabled
    2: queued
    3: working (on other stuff like clean)
    4: working (on installation)
    5: error
    6: installed
    """
    cur = g.conn.cursor()
    cur.execute("""
        CREATE SCHEMA IF NOT EXISTS postgis_baselayers;
        SET search_path TO postgis_baselayers;
        CREATE TABLE IF NOT EXISTS postgis_baselayers (
          name varchar(128) PRIMARY KEY,  
          status int DEFAULT 1 NOT NULL,
          metadata json NOT NULL
        );
        CREATE TABLE IF NOT EXISTS postgis_baselayers_log (
          id SERIAL PRIMARY KEY,
          created TIMESTAMP DEFAULT NOW(), 
          name varchar(128) REFERENCES postgis_baselayers(name),
          task varchar(128) NOT NULL,
          descr varchar(128),
          log TEXT
        );
    """)
    g.conn.commit()

    # Parse and update all the datasets.
    metadata_path = os.path.join(app.root_path, "datasets", "*", "metadata.json")
    for metadata_file in glob(metadata_path):
        try:
            with open(metadata_file) as f:
                json_metadata = json.load(f)
                cur.execute("""
                    INSERT INTO postgis_baselayers (name, metadata) 
                    VALUES (%s, %s) 
                    ON CONFLICT ON CONSTRAINT postgis_baselayers_pkey 
                    DO UPDATE
                        SET metadata = %s;
                """, (json_metadata['name'], json.dumps(json_metadata), json.dumps(json_metadata)))
                g.conn.commit()
        except:
            message = "Update failed."
            return render_template('update.html', **locals())
    message = "Update/initialization completed."
    return render_template('update.html', **locals())

@app.route('/')
def index():
    cur = g.conn.cursor()

    # Check if the 'postgis_baselayers' schema exists. This is where we store 
    # status information for the application. If it doesn't exist (for example
    # when the app is accessed for the first time) then redirect to the 
    # 'update' view, where this schema and tables will be updates/initialized
    # automatically.
    cur.execute("SET search_path TO postgis_baselayers;")
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = 'postgis_baselayers');")
    res = cur.fetchone()
    if not res[0]:
        return redirect(url_for('update'))

    # Fetch the metadata
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            name, status, metadata 
        FROM 
            postgis_baselayers.postgis_baselayers 
        ORDER BY 
            name;
    """)
    datasets = cur.fetchall()
    root_path = app.root_path
    return render_template("index.html", **locals())

@app.route("/dataset/<dataset_name>/")
def dataset(dataset_name):
    """
    Show dataset status information
    """
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            name, status, metadata 
        FROM 
            postgis_baselayers.postgis_baselayers 
        WHERE 
            name=%s 
        LIMIT 1;
    """, (dataset_name,))
    dataset = cur.fetchone()

    base_dir = os.path.join(app.root_path, "datasets", dataset_name)
    with open(os.path.join(base_dir, "README.md")) as f:
        readme = Markup(markdown.markdown(f.read()))

    cur.execute("""
        SELECT 
            created, descr, task, log 
        FROM 
            postgis_baselayers.postgis_baselayers_log 
        WHERE 
            name=%s 
        ORDER BY 
            id DESC 
        LIMIT 6;
    """,(dataset_name,))
    log = cur.fetchall()

    return render_template("dataset.html", **locals())

@app.route("/dataset/<dataset_name>/modify", methods=['POST'])
def enable(dataset_name):
    """
    Installs a dataset
    """
    cur = g.conn.cursor() 
    action = request.values.get("action", None)

    if action == 'Install':
        task = dataset_action(dataset_name, 'install')

    if action == 'Uninstall' or action == 'Clean':
        task = dataset_action(dataset_name, 'clean')

    cur.execute("UPDATE postgis_baselayers.postgis_baselayers SET status=%s WHERE name=%s;", ('2', dataset_name))
    g.conn.commit()

    return redirect(url_for('dataset', dataset_name=dataset_name))

@app.route("/dataset/<dataset_name>/<task_id>/log")
def log(dataset_name, task_id):
    cur = g.conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            name, created, descr, task, log 
        FROM 
            postgis_baselayers.postgis_baselayers_log 
        WHERE 
            name=%s AND
            task=%s
        ORDER BY 
            created DESC 
        LIMIT 1
    """,(dataset_name, task_id))
    log = cur.fetchone()

    return render_template("log.html", **locals())


@huey.task(context=True)
def dataset_action(dataset_name, dataset_action, task=None):
    """
    This is a huey task for enabling a certain dataset. The steps involved in
    this are two-fold. In the directory containing the metadata file, we will:


    1. Download the dataset by running 'make download'
    2. Install the dataset by running 'make install'

    If 'make' returns with code 0 we know everything has worked ok.
    """
    return_code = 0
    message = ''

    # Lock the task based on the dataset name. That way no more than one 
    # task can be run for any dataset (like installing and cleaning it at the 
    # same time, or running two installs simultaneously)
    with huey.lock_task('working-on-dataset-{}'.format(dataset_name)):

        logger = logging.getLogger("task_logger")
        logger.setLevel(logging.DEBUG)
        logstream = StringIO()
        streamhandler = logging.StreamHandler(logstream)
        logger.addHandler(streamhandler)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SET search_path TO postgis_baselayers;")

        try:
            # Prepare the environment in which make can be executed...

            # Create a directory to work in in a subdirectory named after the 
            # dataset within os.environ['POSTGIS_BASELAYERS_WORKDIR']
            base_dir = os.path.join(os.environ['POSTGIS_BASELAYERS_WORKDIR'], dataset_name)
            try: os.makedirs(base_dir)
            except: pass
            if not os.path.isdir(base_dir):
                raise Exception("Base directory '{}' does not exist.".format(base_dir))
            logger.info("Working in base_dir {}".format(base_dir))

            # Copy the relevant files from the application's dataset directory.
            root_dir = os.path.join(app.root_path, 'datasets', dataset_name)
            logger.info("Dataset source dir is {}".format(root_dir))
            for f in os.listdir(root_dir):
                file_path = os.path.join(root_dir,f)
                if os.path.isfile(file_path):
                    shutil.copy2(file_path, base_dir)
                    logger.info("Copied {} to {}".format(file_path, os.path.join(base_dir, f)))

            # Set some additional environment variables for our installation
            # subprocesses.
            subprocess_env = copy.deepcopy(os.environ)
            subprocess_env['PGOPTIONS'] = "-c search_path={},public".format(dataset_name)
            subprocess_env['POSTGRES_URI'] = "postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}".format(**os.environ)
            subprocess_env['POSTGRES_OGR'] = 'PG:"dbname={POSTGRES_DB} host={POSTGRES_HOST} port={POSTGRES_PORT} user={POSTGRES_USER} password={POSTGRES_PASSWORD}"'.format(**os.environ)

            # Either clean/uninstall a dataset or install it
            if dataset_action == 'clean':
                logger.info("\n\n==========\nRunning 'make clean' in {}\n==========".format(base_dir))
                output = subprocess.check_output(["/usr/bin/make","clean"], env=subprocess_env, cwd=base_dir, stderr=subprocess.STDOUT, shell=False, universal_newlines=True, timeout=600)
                logger.info(output)
                return_code = 1

            if dataset_action == 'install':
                logger.info("\n\n==========\nRunning 'make all' in {}\n==========".format(base_dir))
                output = subprocess.check_output(["/usr/bin/make","all"], env=subprocess_env, cwd=base_dir, stderr=subprocess.STDOUT, shell=False, universal_newlines=True, timeout=600)
                logger.info(output)
                return_code = 6

            message = "Successful {}".format(dataset_action)

        except subprocess.CalledProcessError as exc:
            logger.error("ERROR! Subprocess failed. Return code: {} Output: {}".format(exc.returncode, exc.output))
            message = "Failed {}".format(dataset_action)
            return_code = 5

        except Exception as e:
            logger.error("ERROR! An unspecified error occurred: {}".format(e))
            return_code = 5
            message = "Failed {}".format(dataset_action)

        finally:
            # Finally, no matter what happens, create a log entry in the 
            # postgis_baselayers_log table with a log of what's happened 
            # during the execution.
            streamhandler.flush()
            cur.execute("""
                INSERT INTO 
                    postgis_baselayers.postgis_baselayers_log 
                    (name, task, descr, log) 
                VALUES 
                    (%s, %s, %s, %s)
            """, (task.args[0], task.id, message, logstream.getvalue()))
            conn.commit()
            conn.close()

    return return_code

@huey.pre_execute()
def pre_exec_hook(task):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE postgis_baselayers.postgis_baselayers SET status=3 WHERE name=%s;", (task.args[0],))
    conn.commit()
    conn.close()

@huey.post_execute()
def post_exec_hook(task, task_value, exc):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE postgis_baselayers.postgis_baselayers SET status=%s WHERE name=%s;", (task_value, task.args[0]))
    conn.commit()
    conn.close()
