#!/usr/bin/python3

import requests
import json
import asyncio
import json
import math
import time

async def main():
    start_time = time.time()

    #addressString = example()

    end_time = time.time()
    print("total time:")
    print(end_time-start_time)

async def example():
    reverseBBox = ReverseBoundingBox(32, True)
    addressString = await reverseBBox.getCache((51.962739161232776, 7.623842806647303), 125)

    request_time = time.time()

    lut = open("lut.txt", "w")
    lut.write(addressString)
    lut.close()

    return addressString 

class ReverseBoundingBox:
    def __init__(self, resolution=128, verbose=False):
        self.resolution = resolution #resolution is the maximum density of queries used to 
        self.verbose = verbose
        #initiate array of tasks. this is where the parallel queries will run
        self.tasks = [ [None]*self.resolution for i in range(self.resolution) ]
    
    '''
    main function. call this to get one full cache of addresses.
    here, span is the "radius" in Meters.
    center is WGS84 / EPSG4326 (lat,lon) tuple
    '''
    async def getCache(self, center, span):
        northWest = self.offsetCoords(center, span, -span)
        southEast = self.offsetCoords(center, -span, span)
        
        d_lat = abs(southEast[0]-northWest[0])
        d_lon = abs(southEast[1]-northWest[1])
        steps_lat = d_lat/self.resolution
        steps_lon = d_lon/self.resolution

        for i in range(0,self.resolution):
            for j in range(0,self.resolution):
                task = asyncio.create_task(
                    self.query(  
                        southEast[0]+j*steps_lat,
                        southEast[1]+i*steps_lon
                    )
                )
                self.tasks[i][j] = task

        addresses = await self.createAddressList(self.tasks)
        addressList = ""

        for addr in addresses:
            #addressList += f'"coord": [{round(float(addr["lat"]),4)},{round(float(addr["lon"]),4)}], "place": "{addr["display_name"]}"'
            #addressList += "\n"
            #addressString += str(addr)
            #addressString += f'[col: "{addr[1]}", x:{addr[2]} y:{addr[3]}, address:"{addr[0]}"]'  
            
            addressList += f'{{"type": "Feature","properties": {{"place": "{addr["display_name"]}"}},"geometry": {{"coordinates": [{round(float(addr["lon"]),4)},{round(float(addr["lat"]),4)}],"type": "Point"}}}},'  
        #addressString = f'{{places: [{addressList}]}}'
        addressString = f'{{"type": "FeatureCollection","features": [{addressList[:-1]}]}}'
        return addressString


    '''
    offset coords by e meters to the east and n meters towards north.
    returns new coordinate tuple (lat,lon)
    credit: https://stackoverflow.com/a/7478827

    TODO: this is causing a strange offset. to fix!
    '''
    def offsetCoords(self,coords, n, e):        
        lat = coords[0]
        lon = coords[1]
        r_earth = 6371000

        newLat = lat + (n / r_earth) * (180 / math.pi)
        newLon = lon + (e / r_earth) * (180 / math.pi) / math.cos(lat * math.pi/180)
        return (newLat, newLon)
        
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

        for x in range(len(tasks)):   #somehow using i is not behaving correctly..
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

                #no duplicates? cool. create tuple of address and color
                '''
                #define color
                pixNum = len(addresses)
                oghexCol = hex(pixNum)
                hexCol = str(oghexCol)[2:]
                if len(hexCol) < 6:
                    toFill = 6-len(hexCol)
                    for i in range(toFill):
                        hexCol="0"+hexCol
                hexCol = "#"+hexCol
                col = ImageColor.getcolor(hexCol, "RGB")

                #print(str(x) + " " + str(j))
                #print(hexCol + " " + oghexCol)

                #print(current["display_name"])
                #create tuple
                #newAddress = (current["display_name"], col, x, j)
                '''
                addresses.append(current)

        return addresses


asyncio.run(main())