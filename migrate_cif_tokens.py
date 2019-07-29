#!/usr/bin/env python3

import sqlite3
import argparse
import logging
import os
import time

'''
This script may be used to migrate the tokens (and groups) from an old CIF database to a new one.
Use case is when you don't care about the old data, but want to have the same access setup for a new
database. You can 

Stop all cif processes:
systemctl stop cif-httpd.service cif-router.service csirtg-smrt.service

Ensure processes stopped, and no hanging processes:
systemctl status cif-httpd.service cif-router.service csirtg-smrt.service
ps -ef |egrep 'smr[t]|ci[f]'

Move your existing database to a new name and touch the old filename:
mv /var/lib/cif/cif.db /var/lib/cif/cif.db.old
touch /var/lib/cif/cif.db

Now start your services up to get a bootstrap, wait a bit, then stop them:
systemctl start cif-httpd.service cif-router.service csirtg-smrt.service && \
sleep 30 && \
systemctl stop cif-httpd.service cif-router.service csirtg-smrt.service

Run this script to migrate the tokens and groups:
./migrate_cif_tokens.py -o /var/lib/cif/cif.db.old -n /var/lib/cif/cif.db

Then make sure you put all the tokens into the correct locations (as bootstrapping the new database may
overwrite some existing file locations):

cif admin: /home/cif/.cif.yml
cif hunter: /etc/cif/cif-router.yml
csirtg-smrt: /etc/cif/csirtg-smrt.yml
cif httpd (optional): /etc/cif.env

Once that's all set, start your services again (or reboot to make sure all is clean):
systemctl start cif-httpd.service cif-router.service csirtg-smrt.service

No warranties, YMMV, use at your own risk, I won't be held responsible for usage of this code.
'''

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger = logging.getLogger(__name__)
logger.addHandler(handler)


def read_old_tokens(filename):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT id, username, token, expires, read, write, revoked, acl, admin FROM tokens')
    data = c.fetchall()
    conn.close()
    logger.info('Read {} rows of data from tokens'.format(len(data)))
    logger.debug('Read data from tokens: {}'.format(data))
    return data


def read_old_groups(filename):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT id, "group", token_id FROM groups')
    data = c.fetchall()
    conn.close()
    logger.info('Read {} rows of data from tokens'.format(len(data)))
    logger.debug('Read data from tokens: {}'.format(data))
    return data


def write_data(groups, tokens, filename):
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    c.executemany('INSERT OR REPLACE into groups (id, "group", token_id) values (?,?,?)', groups)
    logger.info('Inserted group data to database {}'.format(filename))

    c.execute('select * from groups')
    new_data = c.fetchall()
    logger.info('File {} now contains {} rows in groups'.format(filename, len(new_data)))
    logger.debug('File {} contains group data: {}'.format(filename, new_data))

    c.executemany(
        'INSERT OR REPLACE into tokens (id, username, token, expires, read, write, revoked, acl, admin) values (?,?,?,?,?,?,?,?,?)',
        tokens)
    logger.info('Inserted token data to database {}'.format(filename))

    c.execute('select * from tokens')
    new_data = c.fetchall()
    logger.info('File {} now contains {} rows in tokens'.format(filename, len(new_data)))
    logger.debug('File {} contains token data: {}'.format(filename, new_data))

    input('Press Enter/Return to save and continue, or Ctrl-C to quit without saving')
    conn.commit()


def main():
    stime = time.time()
    parser = argparse.ArgumentParser(
        description='Migrate tokens from one cif.db to a new one',
        epilog='http://xkcd.com/353/')
    parser.add_argument('-o', '--old', dest='old_file_name', required=True,
                        help='Original CIF database containing tokens to migrate')
    parser.add_argument('-n', '--new', dest='new_file_name', required=True,
                        help='New CIF database to migrate tokens to (must exist)')
    parser.add_argument('-d', '--debug', action="store_true", dest='debug',
                        default=False,
                        help='Get debug messages about processing')
    opts = parser.parse_args()

    if opts.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    for filename in [opts.old_file_name, opts.new_file_name]:
        if not os.path.isfile(filename):
            logger.error('File does not exist: {}'.format(filename))
            exit(1)

    tokens = read_old_tokens(opts.old_file_name)
    groups = read_old_groups(opts.old_file_name)

    write_data(groups, tokens, opts.new_file_name)

    runtime = time.time() - stime
    logger.info("Total runtime: {0}".format(runtime))


if __name__ == '__main__':
    main()
