#! /usr/bin/env python
"""Checks drupal sites for updates and inform dev
"""
import boto
from optparse import OptionParser
from prettytable import PrettyTable
import siteOptions as siteOptions
import subprocess

__author__ = "Chaudhry Usman Ali"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Chaudhry Usman Ali"
__email__ = "mani.ali@unb.ca"
__status__ = "Development"

def check_create_update_slot(update_items,project_name,hostname,uri):
    try:
        update_items[project_name]
    except:
        update_items[project_name]={}
    try:
        update_items[project_name][hostname]
    except:
        update_items[project_name][hostname]={}
    try:
        update_items[project_name][hostname][uri]
    except:
        update_items[project_name][hostname][uri]=''

def send_sns_msg_aws(topic_arn, mesg, topicstring):
    try:
        c = boto.connect_sns()
        c.publish(topic_arn, mesg, topicstring)
    except Exception , e:
        print e

topic_string = 'Drupal updates available'
update_items={}

parser = OptionParser()
parser.add_option('-c', '--clear', dest = 'clear_cache', help = 'Clear updates cache before checking for updates.', default = False, action = 'store_true')
parser.add_option('-t','--topic', type = 'string', dest = 'topic_arn', help = 'Destination SNS topic ARN')
(options, args) = parser.parse_args()

tabular_updates_data = PrettyTable(["Project", "Host", "URI", "Class"])
tabular_updates_data.padding_width = 1
tabular_updates_data.align["Project"] = "l"
tabular_updates_data.align["Host"] = "l"
tabular_updates_data.align["URI"] = "l"
tabular_updates_data.align["Class"] = "l"

for hostname, host_information in siteOptions.hosts_to_check.iteritems() :
    for site, site_data in host_information['sites'].iteritems():
        if options.clear_cache:
            p = subprocess.Popen([
                     'ssh',
                     '-i', host_information['key'],
                     host_information['user'] + '@' + hostname,
                     host_information['drush_bin'] +
                      ' --root=' + site_data['root'] +
                      ' --uri=' + site_data['site_uri'],
                      'sql-query',
                      '"DELETE FROM "' + (site_data['cache_update_table'] if 'cache_update_table' in site_data else 'cache_update')
                   ],stdout = subprocess.PIPE)
            p.wait()
        q = subprocess.Popen([
                     'ssh',
                     '-i', host_information['key'],
                     host_information['user'] + '@' + hostname,
                     host_information['drush_bin'] +
                      ' --root=' + site_data['root'] +
                      ' --uri=' + site_data['site_uri'] +
                      ' up',
                      ' -n',
                      '--pipe'
                   ], stdout = subprocess.PIPE)
        q.wait()

        for line in q.stdout:
            update_data = line.split()
            if not update_data[0] in siteOptions.list_of_ignores:
                if site_data['ignores']:
                    if not update_data[0] in site_data['ignores']:
                        project_name=update_data[0]
                        short_uri_string=site_data['site_uri'].replace('http://','')
                        update_data = line.split()
                        check_create_update_slot(update_items,project_name,hostname,short_uri_string)
                        update_items[project_name][hostname][short_uri_string]=update_data[3].replace('-available','')

for project_name, hostdata in sorted(update_items.iteritems()) :
    project_display_switch=False
    for hostname, uridata in hostdata.iteritems() :
        tabular_updates_data.add_row([
                                      project_name if project_display_switch==False else "",
                                      hostname,
                                      "\n".join(key for key in uridata.iterkeys()),
                                      "\n".join(update_class for update_class in uridata.itervalues())
                                      ])
        project_display_switch=True

if not tabular_updates_data.rowcount == 0:
    send_sns_msg_aws(options.topic_arn, topic_string + " :\n" + tabular_updates_data.get_string(), topic_string)
