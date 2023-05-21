#!/usr/bin/python3
import requests
import json
import asyncio
import math
import time

from sanic import Sanic
from sanic.response import text
from cors import add_cors_headers
from options import setup_options

from turfpy.transformation import transform_translate
from geojson import Point, Feature

from nomiInterface import Interface

########################################################################



app = Sanic("mapExcerptServer")
dbInterface = Interface({
        "database":"nominatim",
        "user":"nominatim",
        "password":"1234",
        "host":"127.0.0.1",
        "port":5432
    })

@app.get("/status")
def status(request):
    return text("map-excerpt-server running")

app.static('/reverseHelper.html', "reverseHelper/reverseHelper.html")
app.static('/reverseHelper.css', "reverseHelper/reverseHelper.css")
app.static('/reverseHelper.js', "reverseHelper/reverseHelper.js")

@app.get("/cacheArea")
async def cacheArea(request):
    #prepare arguments
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    format = request.args.get("format")
    span = request.args.get("span")

    if span == None:
        span = 125
    else:
        span = int(span)

    #fetch map material
    reverseBBox = ReverseBoundingBox(40, True)
    #addressString = await reverseBBox.getCache((lat, lon), span)

    nW = reverseBBox.offsetCoords((lat, lon), span, -span)
    sE = reverseBBox.offsetCoords((lat, lon), -span, span)

    return text(dbInterface.reverseBBox(nW[0],nW[1],sE[0],sE[1]))

    #return text(addressString)

app.register_listener(setup_options, "before_server_start")
app.register_middleware(add_cors_headers, "response")


async def main():
    start_time = time.time()

    #addressString = example()

    end_time = time.time()
    print("total time:")
    print(end_time-start_time)

class ReverseBoundingBox:
    def __init__(self, resolution=128, verbose=False):
        self.resolution = resolution #resolution is the maximum density of queries used to 
        self.verbose = verbose
        #initiate array of tasks. this is where the parallel queries will run
        self.tasks = [ [None]*self.resolution for i in range(self.resolution) ]
    
    '''
    offset coords by e meters to the east and n meters towards north.
    returns new coordinate tuple (lat,lon)
    credit: https://stackoverflow.com/a/7478827
    '''
    def offsetCoords(self,coords, n, e):        
        
        #use turfpy
        geojson = f'{{"geometry": {{"coordinates": [{coords[1]},{coords[0]}],"type": "Point"}},"properties": {{}},"type": "Feature"}}'
        feature = json.loads(geojson)
        #north
        offsetFeature = transform_translate(feature, n, direction=365, mutate=True, units="m")
        #east
        offsetFeature = transform_translate(feature, e, direction=90, mutate=True, units="m")

        coords = (offsetFeature["geometry"]["coordinates"][1],offsetFeature["geometry"]["coordinates"][0])
        return coords

        '''
        lat = coords[0]
        lon = coords[1]
        r_earth = 6371000

        newLat = lat + (n / r_earth) * (180 / math.pi)
        newLon = lon + (e / r_earth) * (180 / math.pi) / math.cos(lat * math.pi/180)
        return (newLat, newLon)
        '''
        
    async def query(self,lat,lon):
        queryString = f"http://localhost:8088/reverse.php?format=json&polygon_geojson=1&lat={lat}&lon={lon}"
        res = requests.get(queryString)
        #print(f"querying {x}, {y}")
        response = json.loads(res.text)

        return response
    
    '''
    creates a list of the addresses that were reverse geocoded.
    it removes duplicates so each address is unique. 
    it then assigns a color to each address so it can be used as a LUT
    returns a list of tuples (address, rgb-color, x, y)
    '''
    async def createAddressList(self,tasks):
        addresses = []

        for x in range(len(tasks)):
            j = 0
            for j in range(len(tasks[x])):
                current = await tasks[x][j]
                #look for duplicates first
                duplicate = False

                for n in range(len(addresses)):
                    if addresses[n]["place_id"] == current["place_id"]:
                        duplicate = True

                if duplicate:
                    continue

                addresses.append(current)

        return addresses

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, access_log=True)
