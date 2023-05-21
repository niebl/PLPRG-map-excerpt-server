#!/usr/bin/python3

import queries
import json
import traceback
import sys

###################
def main():
    conn = {
        "database":"nominatim",
        "user":"nominatim",
        "password":"1234",
        "host":"127.0.0.1",
        "port":5432
    }

    reverse = Bridge(conn)
    #reverse.lookup(51.99637,7.55680)
    #reverse.lookupBBox(51.994179, 7.549673, 51.993840, 7.5504026)
    #reversedAddress = reverse.reverseBBox(
    #    51.97288955678147, 
    #    7.614897631740945, 
    #    51.97267740538189, 
    #    7.615381918436157)

    N = float(sys.argv[1])
    W = float(sys.argv[2])
    S = float(sys.argv[3])
    E = float(sys.argv[4])

    reversedAddress = reverse.reverseBBox(N,W,S,E)

    address = json.loads(reversedAddress)["features"][0]["properties"]["address"]
    print(address)

class Interface:
    def __init__(self, args=None, connection=None,):
        if not args:
            if not connection:
                print("no connection given")
                return False
            self.db = connection
        self.db = self.get_connection(args)
        return

    def reverseBBox(self, N, W, S, E):
        #if type(lat) != type(.0) or type(lat) != type(.0):
        #    return False
        #pointSQL = f'ST_SetSRID(ST_Point({lon},{lat}),4326)'
        bboxSQL = f'ST_MakeEnvelope({W}, {S}, {E}, {N},4326)'

        searchDiam = 0.006
        maxRank = 30

        #skipping the maxrank for now
        #this query is based on the Nominatim one (ReverseGeocode.php .> lookupPoint())
        #Due to this snippet, MES is GPL2 licensed
        SQL = f'''
            select 
                place_id,
                parent_place_id,
                rank_address,
                ST_AsGeoJSON(ST_Centroid(geometry)) as geometry,
                hstore_to_json(address) as address_record,
                hstore_to_json(name) as name
            FROM placex
            WHERE geometry && {bboxSQL}
                AND rank_address between 26 and {maxRank}
                and (name is not null or housenumber is not null
                or rank_address between 26 and 27)
                and (rank_address between 26 and 27
                or ST_GeometryType(geometry) != \'ST_LineString\')
                and class not in (\'boundary\')
                and indexed_status = 0 and linked_place_id is null'''

        lowestRank = 30
        places = []

        data = self.db.query(SQL)
        print(data)

        #print(data)
        for point in data:
            print(point)
            place = {
                "placeID": point.get("place_id"),
                "parentPlaceID": point.get("parent_place_id"),
                "rankAddress": point.get("rank_address"),
                "geometry": point.get("geometry"),
                "addressRecord": point.get("address_record"),
                "name": point.get("name"), 
            }
            print(place)
            if place["rankAddress"] < lowestRank:
                lowestRank = place["rankAddress"]
            #maybe do some string processing here..
            places.append(place)

        #IGNORE TIGER DATA FOR NOW

        #Following Block formats as geoJSON
        returnData = []
        for place in places:
            record = self.prepareRecordString(place)

            if record == False:
                continue
            
            geojsonPlace = {
                "type": "Feature",
                "properties" : {"place": record, "place_id": place["placeID"]},
                "geometry": json.loads(place["geometry"])
            }
            returnData.append(geojsonPlace)
        returnGeoJSON = {
            "type": "FeatureCollection", 
            "license": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright", 
            "features":returnData}

        return json.dumps(returnGeoJSON, ensure_ascii=False) #ensure ascii necessary for Umlauts

    '''
    awaits address as dictionary. make sure to convert it from hstore first.
    '''
    def prepareRecordString(self, point):
        if point.get("addressRecord") == None:
            return False

        #deal with this one later.
        if  point["addressRecord"].get("_inherited") != None:
            return False
        
        #init all address pieces
        addressInfo = []

        try:
            p = point["addressRecord"]
            addressInfo.append(p.get("housenumber"))
            addressInfo.append(p.get("street"))
            addressInfo.append(p.get("postcode"))
            addressInfo.append(p.get("city"))
            addressInfo.append(p.get("country"))
            name        =  point.get("name")
            addressInfo.append(name.get("name")) if name else None

            addressInfo = [i for i in addressInfo if i is not None]

            addressString = ", ".join(addressInfo)
        except Exception as error:
            print(traceback.format_exc())
            print(addressInfo)

        '''
        housenr     =  point["addressRecord"].get("housenumber")
        street      =  point["addressRecord"].get("street"    )
        postcode    =  point["addressRecord"].get("postcode"  )
        city        =  point["addressRecord"].get("city"      )
        country     =  point["addressRecord"].get("country"   )
        
        name        =  point.get("name")
        name = name.get("name") if name else None

        addressString = ''
        #TODO: deal with case of missing parts
        addressString += name + ", "        if name else ""
        addressString += housenr            if housenr else ""
        addressString += ", " + street      if street else ""
        addressString += ", " + postcode    if postcode else ""
        addressString += ", " + city        if city else ""
        addressString += ", " + country     if country else ""
        '''
        return addressString

    def get_connection(self, args):
        database=args["database"]
        user=args["user"]
        password=args["password"]
        host=args["host"]
        port=args["port"]

        try:
            session = queries.Session(f"postgresql://{user}:{password}@{host}:{port}/{database}")
            return session

        except:
            print("connection to database failed")
            return False

if __name__ == "__main__":
    main()
