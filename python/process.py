#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import re
import yaml
import csv
import requests

from contextlib import closing

import datetime as DT
from datetime import datetime, date, time

#from operator import itemgetter
#from collections import OrderedDict
from sortedcontainers import SortedDict

# User Agent String
USER_AGENT_STRING = "Python/process-problematic-feeds @cisene@podcastindex.social"

# Data url
DATA_CSV_SOURCE = "https://public.podcastindex.org/podcastindex_problematic_feeds.csv"

DATA_YAML_DEST = '../yaml/podcastindex-problematic-feeds.yaml'
DATA_YAML_FEEDS = '../yaml/podcastindex-problematic-feeds-collections.yaml'

def writeYAML(filepath, contents):
  s = yaml.safe_dump(
    contents,
    indent=2,
    width=1000,
    canonical=False,
    sort_keys=False,
    explicit_start=False,
    default_flow_style=False,
    default_style='',
    allow_unicode=True,
    line_break='\n'
  )
  with open(filepath, "w") as f:
    f.write(s.replace('\n- ', '\n\n- '))

def readYAML(filepath):
  contents = None
  data = None
  if os.path.isfile(filepath):
    fp = None

    try:
      fp = open(filepath)
      contents = fp.read()
      fp.close()

    finally:
      pass

  if contents != None:
    data = yaml.safe_load(contents)

  return data


def httpGET(url):
  result = None
  headers = {
    'User-Agent': USER_AGENT_STRING,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
  }
  r = requests.get(url, headers=headers)
  if r.status_code == 200:
    result = r.text
  else:
    print(r.status_code)
  return result

def convertEpochToISO(epoch):
  #dt = datetime.utcfromtimestamp(epoch)
  dt = datetime.fromtimestamp(epoch)
  isodate = dt.strftime("%Y-%m-%d")
  #isodate = dt.datetime.fromtimestamp(epoch, datetime.UTC)
  return isodate

def reasonResolver(reason):
  reasons = {
    1: 'Spam',
    2: 'AI Slop',
    3: 'Illegal',
    5: 'Malicious',
    6: 'Hijack',
  }
  if reason >= 1 and reason <= 6: 
    reason = reasons[reason]
  else:
    reason = 'unknown'

  return reason

def renderSlugFromUrl(url):
  result = None
  data = url
  data = re.sub(r"^http(s)?\x3a\x2f\x2f", "", data, flags=re.IGNORECASE)
  data = re.sub(r"\x2f.*$", "", data, flags=re.IGNORECASE)
  parts = re.split(r"\x2e", data, flags=re.IGNORECASE)
  parts.reverse()

  tldList = [
    'agency',
    'ai',
    'app',
    'au',
    'blog',
    'cc',
    'click',
    'cloud',
    'co',
    'com',
    'computer',
    'coop',
    'de',
    'dev',
    'digital',
    'dk',
    'ee',
    'es',
    'eu',
    'fi',
    'fm',
    'fr',
    'fun',
    'id',
    'io',
    'it',
    'jp',
    'kz',
    'me',
    'media',
    'net',
    'news',
    'nl',
    'no',
    'nz',
    'online',
    'org',
    'pl',
    'pro',
    'ro',
    'ru',
    'se',
    'space',
    'stream',
    'tech',
    'top',
    'tv',
    'ua',
    'us',
    'vn',
    'website',
    'xyz',
  ]

  wtfTLDs = [
    'br',
    'in',
    'mx',
    'pe',
    'uk',
  ]


  if parts[0] in tldList:
    result = f"{parts[1]}{parts[0]}"
  else:
    if parts[0] in wtfTLDs:
      result = f"{parts[2]}{parts[1]}{parts[0]}"
  return result

def resolveFeedSource(url):
  result = None
  if re.search(r"^https\x3a\x2f\x2fwww\x2espreaker\x2ecom\x2fshow\x2f(\d{3,9})\x2fepisodes\x2ffeed", url, flags=re.IGNORECASE):
    result = 'spreakercom'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2ebuzzsprout\x2ecom\x2f(\d{3,9})\x2erss", url, flags=re.IGNORECASE):
    result = 'buzzsproutcom'

  if re.search(r"^https\x3a\x2f\x2frss\x2ebuzzsprout\x2ecom\x2f(\d{3,9})\x2erss", url, flags=re.IGNORECASE):
    result = 'buzzsproutcom'

  if re.search(r"^https\x3a\x2f\x2f([a-z0-9\x2d\x5f]{1,})\x2epodbean\x2ecom\x2ffeed\x2exml", url, flags=re.IGNORECASE):
    result = 'podbeancom'

  if re.search(r"^https\x3a\x2f\x2ffeed\x2epodbean\x2ecom\x2f([a-z0-9\x2d\x5f]{1,})\x2ffeed\x2exml", url, flags=re.IGNORECASE):
    result = 'podbeancom'

  if re.search(r"^https\x3a\x2f\x2frss\x2epodomatic\x2enet\x2frss\x2f([a-z0-9\x2d\x2e\x5f]{1,})\x2frss2\x2exml", url, flags=re.IGNORECASE):
    result = 'podomaticcom'

  if re.search(r"^https\x3a\x2f\x2f([a-z0-9\x2e\x2d\x5f]{1,})\x2epodomatic\x2ecom\x2frss2\x2exml", url, flags=re.IGNORECASE):
    result = 'podomaticcom'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2ehubhopper\x2ecom\x2f([a-f0-9]{32})\x2erss", url, flags=re.IGNORECASE):
    result = 'hubhoppercom'

  if re.search(r"^https\x3a\x2f\x2ffeed\x2eausha\x2eco\x2f([a-z0-9]{12})", url, flags=re.IGNORECASE):
    result = 'aushaco'

  if re.search(r"^https\x3a\x2f\x2fmedia\x2erss\x2ecom\x2f([a-z0-9\x2d\x5f]{1,})\x2ffeed\x2exml", url, flags=re.IGNORECASE):
    result = 'rsscom'

  if re.search(r"^https\x3a\x2f\x2ffeed\x2efirstory\x2eme\x2frss\x2fuser\x2f([a-z0-9\x2d\x5f]{25})", url, flags=re.IGNORECASE):
    result = 'firstoryme'

  if re.search(r"^https\x3a\x2f\x2fanchor\x2efm\x2fs\x2f([a-f0-9]{3,12})\x2fpodcast\x2frss", url, flags=re.IGNORECASE):
    result = 'anchorfm'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2etransistor\x2efm\x2f([a-z0-9\x2d\x5f]{1,})", url, flags=re.IGNORECASE):
    result = 'transistorfm'

  if re.search(r"^https\x3a\x2f\x2f([a-z0-9\x2d\x5f]{1,})\x2epodigee\x2eio\x2ffeed\x2f(mp3)", url, flags=re.IGNORECASE):
    result = 'podigeeio'

  if re.search(r"^https\x3a\x2f\x2fapi\x2eriverside\x2ecom\x2fhosting\x2f([a-z0-9\x2d\x5f]{1,})\x2erss", url, flags=re.IGNORECASE):
    result = 'riversidecom'

  if re.search(r"^https\x3a\x2f\x2f([a-z0-9\x2d\x5f]{1,})\x2eletscast\x2efm(\x2f)?", url, flags=re.IGNORECASE):
    result = 'letscastfm'

  if re.search(r"^https\x3a\x2f\x2fpinecast\x2ecom\x2ffeed\x2f([a-z0-9\x2d\x5f]{1,})", url, flags=re.IGNORECASE):
    result = 'pinecastcom'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2emegaphone\x2efm\x2f([a-z0-9]{1,})", url, flags=re.IGNORECASE):
    result = 'megaphonefm'

  if re.search(r"^https\x3a\x2f\x2frss\x2ecastbox\x2efm\x2feverest\x2f([a-f0-9]{32})\x2exml", url, flags=re.IGNORECASE):
    result = 'castboxfm'

  if re.search(r"^https\x3a\x2f\x2f([a-z0-9\x2d\x5f]{1,})\x2ejellypod\x2ecom\x2frss", url, flags=re.IGNORECASE):
    result = 'jellypodcom'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2esundays\x2enews\x2f([a-z0-9\x2d\x5f]{1,})\x2exml", url, flags=re.IGNORECASE):
    result = 'sundaysnews'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2efastcast\x2eai\x2f([a-z0-9\x2d\x5f]{1,})\x2exml", url, flags=re.IGNORECASE):
    result = 'fastcastai'

  if re.search(r"^https\x3a\x2f\x2ffeeds\x2ecastos\x2ecom\x2f([a-z0-9\x2d\x5f]{1,})", url, flags=re.IGNORECASE):
    result = 'castoscom'


  if result == None:
    result = renderSlugFromUrl(url)


  return result



def main():

  results = readYAML(DATA_YAML_DEST)
  feeds = readYAML(DATA_YAML_FEEDS)

  if results == None:
    results = {}
    results['dates'] = {}

  if feeds == None:
    feeds = {}
    feeds['feeds'] = {}

  data = httpGET(DATA_CSV_SOURCE)

  csvReader = csv.reader(data.split('\n'),  delimiter=',', dialect=csv.excel)
  header = next(csvReader)
  # id,feedId,reason,updatedOn,note,url,generator,author,itunesOwnerName,itunesId

  #idx_id = header.index("id")
  #idx_feedId = header.index("feedId")
  idx_reason = header.index("reason")
  idx_updatedOn = header.index("updatedOn")
  #idx_note = header.index("note")
  idx_url = header.index("url")

  fields = [
    idx_reason,
    idx_updatedOn,
    idx_url,
  ]

  for row in csvReader:
    if (row):
      for field in fields:
        value = row[field]

        if field == idx_reason:
          value = reasonResolver(int(value))
          reasonKey = value

        if field == idx_updatedOn:
          value = convertEpochToISO(int(value))
          dateKey = value

        if field == idx_url:
          url = value
          value = resolveFeedSource(value)
          if value == None:
            print(f"Unresolved url '{value}'")
            #exit(0)
            continue
          feedSourceKey = value


      if dateKey not in results['dates']:
        results['dates'][dateKey] = {}
        results['dates'][dateKey]['Total'] = 0

      if results['dates'][dateKey]['Total'] > 0:
        continue

      if reasonKey not in results['dates'][dateKey]:
        results['dates'][dateKey][reasonKey] = {}

      if feedSourceKey not in results['dates'][dateKey][reasonKey]:
        results['dates'][dateKey][reasonKey][feedSourceKey] = 0

      results['dates'][dateKey][reasonKey][feedSourceKey] += 1

      if feedSourceKey not in feeds['feeds']:
        feeds['feeds'][feedSourceKey] = []

      if url not in feeds['feeds'][feedSourceKey]:
        if not re.search(r"\x5fconflict$", url, flags=re.IGNORECASE):
          feeds['feeds'][feedSourceKey].append(url)


  print("Sorting dates ..")
  sorted_dates = dict(sorted(results['dates'].items(), key=lambda item: item[0]))
  results['dates'] = sorted_dates

  print("Completing date counts ..")
  for date_date in results['dates']:
    if results['dates'][date_date]['Total'] == 0:
      value_total = 0
      for topic in results['dates'][date_date]:
        if topic == "Total":
          continue

        sorted_topic = dict(sorted(results['dates'][date_date][topic].items(), key=lambda item: item[0]))
        #print(sorted_topic)
        results['dates'][date_date][topic] = sorted_topic

        for domain in results['dates'][date_date][topic]:
          value_total += results['dates'][date_date][topic][domain]
          pass

      if value_total != 0:
        results['dates'][date_date]['Total'] = value_total
        print(f"\t{date_date}: {value_total}")

  print("Sorting files ..")
  sorted_files = dict(sorted(feeds['feeds'].items(), key=lambda item: item[0]))
  feeds['feeds'] = sorted_files

  for domain in feeds['feeds']:
    sorted_domain = sorted(feeds['feeds'][domain])
    feeds['feeds'][domain] = sorted_domain

  #sorted(results)
  writeYAML(DATA_YAML_DEST, results)
  print(f"Wrote: {len(results['dates'])} dates ..")

  sorted(feeds)
  writeYAML(DATA_YAML_FEEDS, feeds)
 

if __name__ == '__main__':
  main()
