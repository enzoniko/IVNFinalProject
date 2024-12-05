#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import json
import re

import pyproj

import os, requests
# from datetime import datetime
#from datetime import timedelta
#import numpy as np
#import wavio

log_path = "./logs_log.txt"
read_commit_id = "commit_id.log"

DEBUG = True
ego_class = 12

from os.path import join
# import glob
# import numpy as np
import os
import json
import os, sys


# import math
# import struct
import base64
# from hashlib import sha256
# from datetime import datetime
# import open3d as o3
import zipfile, io

SIGNATURE = 120

series = { 'series' : {
                'version' : '1.2',
    	        'unit' : 0x02230000,
    	        'x' : 0,
    	        'y' : 0,
    	        'z' : 0,
    	        'r' : 0,
                't0' : 1509328800000000,
                't1' : 1609470000000000,
                'workflow' : 0,
                'signature' : SIGNATURE
             }
}

sd = {
        'smartdata' : 
        [
            {
                'version' : '1.2',
                'unit'    : 0x02230000,
                'value'   : 0,
                'error'   : 0,
                'confidence' : 0,
                "x" : 0,
                "y" : 0,
                "z" : 0,
                't' : 1509391500000000,
                'dev' : 99991581,
                'signature' : SIGNATURE
            }
        ]
    }

entry_regex = re.compile(
    r"u=\{[^}]+\}=>"
    r"(?P<u>\d+),"
    r"d=(?P<d>\d+),"
    r"t=(?P<t>\d+),"
    r"sig=(?P<sig>\d+)\)?"
    r"=\{(?P<v>[^\[\{]*?)(\[(?P<list_v>[^\]]*)\])?\}"
)
'''
entry_regex = re.compile(
    r"u=\{[^}]+\}=>"
    r"(?P<u>\d+),"
    r"d=(?P<d>\d+),"
    r"t=(?P<t>\d+)\)?"
    r"=\{(?P<v>[^\[\{]*?)(\[(?P<list_v>[^\]]*)\])?\}"
)
'''

def convert_to_valid_json(text):
    # Replace single quotes with double quotes and ensure keys are double-quoted
    text = text.replace("'", '"')
    text = re.sub(r'(\w+)=', r'"\1":', text)
    return text
    
def read_file_as_string(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def parse_unit(_u):
    # UNCOMMENT THIS SECTION FOR HEXADECIMAL SUPPORT
    '''
    # Ensure the hexadecimal is 32 bits long
    if len(hex_value) != 10:  # 0x + 8 hex digits = 10 characters
        raise ValueError("Hexadecimal value must be 32 bits long.")

    # Convert the hexadecimal to a 32-bit integer
    value = int(hex_value, 16)

    '''
    # Extract bits for each variable
    length = _u & 0xFFFF           # Bits 0-15
    subtype = (_u >> 16) & 0xFF    # Bits 16-23
    type_ = (_u >> 24) & 0x1F      # Bits 24-28 (5 bits)
    multi = (_u >> 29) & 0x03      # Bit 30
    si = (_u >> 31) & 0x01         # Bit 31

    if si: 
        return  {
            "length": -1,
            "subtype": -1,
            "type": -1,
            "multi": -1,
            "si": si
        }
    else:
        return {
            "length": length,
            "subtype": subtype,
            "type": type_,
            "multi": multi,
            "si": si
        }

def _egos(entries):
    _e = []
    for e in entries:
        unit = parse_unit(e['entry']['u'])
        if (unit['si'] == 1):
            continue
        else:
            if (unit['subtype'] == ego_class):
                _e.append(e)

    return _e
    
def _t0(entries):
    return entries[0]['entry']['t']

def count_occurrences(dev, entries):
    count = 0
    for e in entries:
        if (dev == e['entry']['d']):
            count = count + 1
    return count

def first_dev(entries):
    return entries[0]['entry']['d']
    

HOST = "iot.ufsc.br"
create_url ='https://'+HOST+'/api/create.php'
put_url = "https://"+HOST+"/api/put.php"
get_url = "https://"+HOST+"/api/get.php"

wgs84_to_ecef = pyproj.Transformer.from_crs(
    {"proj":'latlong', "ellps":'WGS84', "datum":'WGS84'},
    {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
    )

ecef_to_wgs84 = pyproj.Transformer.from_crs(
    {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
    {"proj":'latlong', "ellps":'WGS84', "datum":'WGS84'},
    )

# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.poolmanager import PoolManager

MY_CERTIFICATE = ['2066765E295F21E42842DE815291C91AB283C31C.pem', '2066765E295F21E42842DE815291C91AB283C31C.key']
#MY_CERTIFICATE = ['./sdav_cert/sdav.pem', './sdav_cert/sdav.key']

def debug(*args):
    if (DEBUG):
        print(*args)
        
    output = ' '.join(map(str, args))
    output = output + "\n"
    with open(log_path, "a") as log_file:
        log_file.write(output)

def send_to_iot(url, content):
    session = requests.Session()
    session.headers = {'Content-type' : 'application/json'}
    session.cert = MY_CERTIFICATE
    response = session.post(url, json.dumps(content))
    rc = response.status_code
    debug(rc)
    return rc

import time

file_path = './smartdata/logs/clean_sniffer.log'
data = read_file_as_string(file_path)
start_string = "Log Start:\n"
log_start = data.index(start_string)

sigs = []
try:
    with open("veh_sigs.txt", "r") as f:
        sigs = f.read().split("\n")[:-1]
    sigs = [int(i) for i in sigs]
except Exception as err:
    debug("veh_sigs.txt not found or empty", err," ... skipping file")

data = data[log_start+len(start_string):]

entries = []
for match in entry_regex.finditer(data.replace(",\n\t]","\n\t]")):
    if match.group("list_v"):
        list_v = match.group("list_v").strip()
        # Convert the string list to an actual list of dictionaries
        list_v = convert_to_valid_json(f"[{list_v}]")
        list_v = json.loads(list_v)
        entry = {
            "u": int(match.group("u")),
            "d": int(match.group("d")),
            "t": int(match.group("t")),
            "v": list_v
        }
    else:
        entry = {
            "u": int(match.group("u")),
            "d": int(match.group("d")),
            "t": int(match.group("t")),
            "v": float(match.group("v")) if match.group("v").strip() else None
        }
    entries.append({"entry": entry})

# Convert the entries list to JSON
json_output = json.dumps(entries, indent=4)

egos = _egos(entries)

t0 = _t0(entries)
debug("t0:",t0)
d0 = first_dev(entries)
debug("first dev:",d0)

simu_length = count_occurrences(d0, entries)
ts_step = 100000

series_t0 = t0 - 1000000
series_tf = int(time.time()*1000000)

series['series']['t0'] = series_t0
series['series']['t1'] = series_tf

cpp_logs_path = "./smartdata/logs/"
python_logs_path = "./external/carlav2/logs/"
context_path = "./context.json"

def finish_context():
    commit_id = ""
    with open(read_commit_id, "r") as f:
        commit_id = f.read()
    with open(context_path, "r") as f:
        context = json.loads(f.read())
    
    for s in context["vehicles"][0]["sensors"]:
        for r in s["readings"]:
            r["t0"] = series_t0
            r["tf"] = series_tf
            r["signature"] = context["vehicles"][0]["id"]
            r["domain"] = "sdav"

    for mv in context["vehicles"][0]["motion_vectors"]:
        mv["t0"] = series_t0
        mv["tf"] = series_tf
        mv["signature"] = context["vehicles"][0]["id"]
        mv["domain"] = "sdav"
    
    if ("actuation" in context["vehicles"][0]):
        for a in context["vehicles"][0]["actuation"]:
            a["t0"] = series_t0
            a["tf"] = series_tf
            a["signature"] = context["vehicles"][0]["id"]
            a["domain"] = "sdav"
    
    if ("telemetry" in context["vehicles"][0]):
        for t in context["vehicles"][0]["telemetry"]:
            t["t0"] = series_t0
            t["tf"] = series_tf
            t["signature"] = context["vehicles"][0]["id"]
            t["domain"] = "sdav"

    context["id"] = commit_id
    if (len(sigs) > 0):
        context["sigs"] = sigs

    with open(context_path, "w") as f:
        f.write(json.dumps(context, indent=4))

try:
    finish_context()
except Exception as err:
    debug("context.json not found or error in parse", err," ... skipping file")


files_to_zip = []
files = os.listdir(cpp_logs_path)
for f in files:
    if (".gitignore" in f):
        continue
    files_to_zip.append(cpp_logs_path+f)

files = os.listdir(python_logs_path)
for f in files:
    if (".gitignore" in f):
        continue
    files_to_zip.append(python_logs_path+f)

files_to_zip.append(context_path)

zip_unit = 4 << 24 | 1

def convert_bytes_to_json_blob(bytes):
    binstr = base64.b64encode(bytes)
    aux = str(binstr)
    return aux[2 : len(aux)-1]

memfile = io.BytesIO()
with zipfile.ZipFile(memfile, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    for file in files_to_zip:
        try:
            zf.write(file, compress_type=zipfile.ZIP_DEFLATED)
        except Exception as error:
            debug("cannot add file", file, error)

data = memfile.getvalue()

debug("sending logs, unit=", zip_unit)
series['series']["unit"] = zip_unit
series["series"]["dev"] = 0
debug("series:", series)
send_to_iot(create_url, series)

sd['smartdata'][0]['unit'] = zip_unit
sd['smartdata'][0]['dev'] = 0
sd['smartdata'][0]['t'] = t0
sd['smartdata'][0]['value'] = convert_bytes_to_json_blob(data)
debug("SmartData")
send_to_iot(put_url, sd)

# with open("test.zip", "wb") as f:
#     f.write(data)

# def get_series(unit, t0, tf, dev, sig):
#     global session

#     get_series = { "series": {
#         "version"    : "1.2",
#         "unit"       : unit,
#         "t0"         : t0,
#         "t1"         : tf,
#         "workflow"   : 0,
#         "dev"        : dev, # Unlike version 1.1, dev must be defined in series.  If there is another device with same unit, another series must be created.
#         "signature"  : sig
#     }}
#     session = requests.Session()

#     # Create the series
#     session.headers = {'Content-type' : 'application/json'}
#     session.cert = MY_CERTIFICATE
#     response = session.post(get_url, json.dumps(get_series), verify=False)
#     resp = response.status_code
#     if resp != 200:
#         print(resp, "Get failed, aborting test...")
#         return False, ""
#     else:
#         print("Get V1.2 - OK")
#         return True, response.text

# def test_zip_get():

#     print(series_t0,series_tf)
#     res = get_series(zip_unit, series_t0, series_tf, 0, 120)[1]
#     res = json.loads(res)
#     #print(res)
#     zip_str = res["series"][0]["value"]
#     print(len(zip_str))
#     zip_bin = base64.b64decode(zip_str)
#     with open("test_get.zip", "wb") as f:
#         f.write(zip_bin)

# test_zip_get()
