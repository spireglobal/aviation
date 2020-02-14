import csv, requests, datetime, time, json, pandas as pd
from xml.dom import minidom

#global variable for getting filename created at callstream
FILENAME = []
JSONDict = []
#counter of target_updates
tu_count = 0
terr_count = 0
sat_count = 0

#reads data from XML file
class Xml:

    def __init__(self, xmlfile, tagname):
        self.xml = xmlfile
        self.tagname = tagname

    def xml_file(self):
        xmldoc = minidom.parse(self.xml)
        xmlitems = xmldoc.getElementsByTagName(self.tagname)
        #append xmlnodes into xml_params
        xml_params = [item.childNodes[0].nodeValue for item in xmlitems]
        xml_params.append(runtime)
        return xml_params

#class to access Spire Datastream API
#inherits from XML
class Stream():

    def __init__(self, url, token, timeout):
        self.url = url
        self.token = token
        self.timeout = int(timeout)

    @staticmethod
    #will return time
    def get_time():
        time_now = datetime.datetime.now()
        time_converted = time_now.strftime("%m-%d-%Y_%H-%M-%S_%p")
        return time_converted

    #call datastream and output to new file
    def call_stream(self):
        try:
            #paramaters for call
            headers = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(self.token)}
            timeout = time.time() + self.timeout

            #calling datastream
            with requests.get(self.url, headers=headers, stream=True) as r:
                with open('ds_json/' + 'ds:' + self.get_time() + '.json', 'w') as json_file:

                    #global declaration
                    global tu_count
                    FILENAME.append(json_file.name)

                    #reading through JSON hashtables
                    for line in r.iter_lines(decode_unicode=True):
                        tu_count += 1
                        if time.time() < timeout:
                            #msg is for further parsing, use loads
                            msg = json.loads(line)
                            data = msg['target']
                            JSONDict.append(data)
                            #dumps is for pretty print
                            json_pprint = json.dumps(msg, indent=2)
                            json_file.write(json_pprint)
                            if pp_print_stream == 'Y':
                                print(json_pprint)
                            elif pp_print_stream == 'N':
                                pass
                            else:
                                print(json_pprint)

                            #looping through dict objects and counting useful statistics for target_updates
                            data = msg['target']
                            JSONDict.append(data)

                        else:
                            r.close()
        except (AttributeError, KeyError):
            pass

#class for Dictionary object that holds our parsed JSON string objects**
#inherit attributes from Stream
class Csv:

    #attributes for class
    def __init__(self, JSONDict):
        self.JSONDict= JSONDict

    def json2csv(self):
        try:
            time_now = datetime.datetime.now()
            time_converted = time_now.strftime("%m-%d-%Y_%H-%M-%S_%p")

            with open( 'ds_csv/' +'ds:' +  time_converted +'.csv', 'w', newline='') as csv_file:
                fieldnames=['icao_address', 'timestamp', 'latitude', "longitude", "altitude_baro", "heading",
                "ground_speed", "vertical_rate",'squawk_code' ,"on_ground", "callsign",  "tail_number", "collection_type",
                "flight_number", "origin_airport_iata", "destination_airport_iata"]
                csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                csv_writer.writeheader()
                for key in self.JSONDict:
                    for item in key:
                        csv_writer.writerow(key)
        except json.decoder.JSONDecodeError:
            pass

#inherit attribute from Csv
class Statistics(Csv):

    #attributees for class
    def __init__(self, terrestrial, satellite, total):
        super().__init__(JSONDict)
        self.terrestrial = terrestrial
        self.satellite = satellite
        self.total = total

    def statistics(self):

        #global declarations for assignments
        global terr_count
        global sat_count

        for key in self.JSONDict:
            for item in key:
                if item == 'collection_type' and key[item] == 'terrestrial':
                    terr_count += 1
                elif item == 'collection_type' and key[key] == 'satellite':
                    sat_count += 1


if __name__ == '__main__':

    #program runtime as input
    runtime = int(input('Enter program timeout, in seconds: '))
    output_csv = input('Do you want a CSV output file? (Y/N) : ')
    pp_print_stream = input('Do you want to see target_updates printed to command line during call? (Y/N) : ')

    #instance of XML file reading
    xml_arg = Xml('ds.xml', 'item')

    #instance of stream arguments
    xml_args_pass = xml_arg.xml_file()
    stream_call = Stream(xml_args_pass[0], xml_args_pass[1], xml_args_pass[2])
    stream_call.call_stream()


    #conditional printout for CSV file
    if output_csv == 'Y':
        #instance of Csv
        csv_call = Csv(JSONDict)
        csv_call.json2csv()
    elif output_csv == 'N':
        pass

    #instance of Statistics
    statistics_call = Statistics(terr_count, sat_count, tu_count)
    statistics_call.statistics()
    #print statements for statistics
    print('Total Target Updates: {}'.format(tu_count))
    print('Terrestrial Target Updates: {}'.format(terr_count))
    print('Satellite Target Updates: {}'.format(sat_count))
    print('Stream Token Updates:', tu_count - (terr_count + sat_count))
    print('Query Paramters: {}'.format(xml_args_pass))
