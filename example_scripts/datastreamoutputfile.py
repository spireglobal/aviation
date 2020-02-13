import csv, requests, datetime, time, json
from xml.dom import minidom

#program runtime as input
runtime = int(input('Enter program timeout, in seconds: '))

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

    def call_stream(self):
        try:

            headers = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(self.token)}
            timeout = time.time() + self.timeout
            with requests.get(self.url, headers=headers, stream=True) as r:
                with open('datastream:' + self.get_time() + '.json', 'w') as json_file:
                    for line in r.iter_lines(decode_unicode=True):
                        if time.time() < timeout:
                            msg = json.loads(line)
                            json_pprint = json.dumps(msg, indent=2)
                            print(json_pprint)
                            json_file.write(json_pprint)
                        else:
                            r.close()
        except AttributeError:
            pass


if __name__ == '__main__':
    #instance of XML file reading
    xml_arg = Xml('ds.xml', 'item')
    #instance of stream arguments
    xml_args_pass = xml_arg.xml_file()
    stream_call = Stream(xml_args_pass[0], xml_args_pass[1], xml_args_pass[2])
    #print statements for call
    print(xml_args_pass)
    print(stream_call.call_stream())
