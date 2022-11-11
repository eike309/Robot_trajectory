from ctypes import sizeof
import xml.etree.ElementTree as ET
import csv
import cv2 as cv
import os
import argparse
#from operator import index


def parse_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('-m','--mcf', type=str, required=True, help = "path to mcf file of map")
    parser.add_argument('-l','--log', type=str, required=True, help = "path to logfile of robot")
    parser.add_argument('-s','--start', type=str, required=True, help = "starttime of wanted trajectory, format: 08:30")
    parser.add_argument('-e','--end', type=str, required=True, help = "endtime of wanted trajectory, format: 08:30")
    parser.add_argument('-i','--imgname', type=str, nargs="?", default="Trajectory", help = "name of image to save trajectory in, no .png needed, either specify this value or dont enter the argument at all")
    args=parser.parse_args()
    if args.imgname == False:
        args.imgname = "Trajectory"
    return args

def parsePositionAndTime(logfile, mapOrigin, cellsize):
    positionList = []
    timeList = []
    with open(logfile) as csv_file:
        sanitized_input= [data.replace('\x00', '') for data in csv_file]
        csv_reader = csv.reader(sanitized_input, delimiter=' ')
        for row in csv_reader:
            if len(row) >= 5:
                xRobot = int(round(float(row[3])/cellsize))
                yRobot = int(round(float(row[4])/cellsize))
                xImage = mapOrigin[0] + xRobot
                yImage = mapOrigin[1] - yRobot
                positionOnImage = (xImage,yImage)
                positionList.append(positionOnImage)
                timeList.append(row[1])
    return positionList, timeList

def drawTrajectory(positionList,img):
    position_point_former = [0,0]
    position_point_latter = [0,0]
    line_count = 0
    for i in positionList:
        if line_count == 0:
                    position_point_former[0] = i[0]
                    position_point_former[1] = i[1]
                    start_point = (position_point_former[0],position_point_former[1])
                    cv.circle(img,start_point, 15, (0,128,0), -1)
                    line_count += 1
        else:
            position_point_latter[0] = i[0]
            position_point_latter[1] = i[1]
            latter_point = (position_point_latter[0],position_point_latter[1])
            former_point = (position_point_former[0],position_point_former[1])
            if position_point_latter != position_point_former:
                cv.line(img,former_point, latter_point,(0,0,128),1,cv.LINE_8,0)
            position_point_former[0] = i[0]
            position_point_former[1] = i[1]
            line_count += 1
            if line_count == len(positionList):
                cv.circle(img,latter_point, 15, (128,0,0), -1)

def slicePositionList(positionList, timeList,starttime, endtime):
    #search the timeList for the input times (in hours and minutes) and choose the first time
    # which has similar hours and minutes
    for i in timeList:
        if i[:5] == starttime[:5]:
            startIndex = timeList.index(i)
            break
    for j in timeList:
        if j[:5] == endtime[:5]:
            endIndex = timeList.index(j)
            break
    slicedPositionList = positionList[startIndex:endIndex+1]
    return slicedPositionList

# Bild aus xml lesen, xml aus mcf lesen

def main():
    #input arguments from commandline
    inputs = parse_args()
    mcf = inputs.mcf
    logfile = inputs.log
    starttime = inputs.start
    endtime = inputs.end
    imgname = inputs.imgname

    directoryPath = os.path.dirname(os.path.abspath(mcf))
    #parse mcf and get name of xml
    MCFtree = ET.parse(mcf)
    MCFroot = MCFtree.getroot()
    for mapXML in MCFroot.iter('StaticMap'):
        mapXMLname = mapXML.text

    #parse xml and get name of map image, cellsize and maporigin
    XMLtree = ET.parse(directoryPath + "/" + mapXMLname)
    XMLroot = XMLtree.getroot()
    for staticMap in XMLroot.iter('Image'):
        staticMapName = staticMap.text
    img = cv.imread(directoryPath + "/" + staticMapName)

    for X in XMLroot.iter('X'):
        xMapOrigin = int(X.text)
    for Y in XMLroot.iter('Y'):
        yMapOrigin = int(img.shape[0]-int(Y.text))
    mapOrigin = (xMapOrigin,yMapOrigin)
    for Cell in XMLroot.iter('CellSize'):
        cellsize = float(Cell.text)
    
    #parse the positions(and convert the to the right KOS) and times from the CSV file to lists
    positionList, timeList = parsePositionAndTime(logfile, mapOrigin, cellsize)
    slicedPositionList = slicePositionList(positionList, timeList,starttime, endtime)
    #draw lines between the positions
    drawTrajectory(slicedPositionList,img)

    cv.imwrite(imgname + ".png", img)
    cv.imshow('',img)
    k = cv.waitKey(0)

if __name__ == "__main__":
    main()