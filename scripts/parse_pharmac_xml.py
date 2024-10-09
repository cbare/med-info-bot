import xml.etree.ElementTree as ET

tree = ET.parse('data/HML_2024-10-01.xml')
root = tree.getroot()


ns = {"": "http://schedule.pharmac.govt.nz/2006/07/Schedule#"}

section = root.find('Section', ns)

for atc1 in section.findall('ATC1', ns):
    atc1_name = atc1.find('Name', ns).text
    for atc2 in atc1.findall('ATC2', ns):
        atc2_name = atc2.find('Name', ns).text
        for atc3 in atc2.findall('ATC3', ns):
            atc3_name = atc3.find('Name', ns).text

            for med in atc3.findall('Chemical', ns):
                print(med.attrib['ID'], atc1_name, atc2_name, atc3_name, med.find('Name', ns).text)
