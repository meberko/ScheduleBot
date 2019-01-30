import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import csv

DEFAULT_DATA_DIR = './Data/'
DAYS = ['M','T','W','R','F']
SLOT_RANGE = 65
SLOT_LIST = []

class Slot:
    def __init__(self,day,start,end):
        self.day = day
        self.start = start
        self.end = end

class Lab:
    def __init__(self,type,section,slot):
        self.type = type
        self.section = section
        self.slot = slot

class Student:
    def __init__(self,name,free_list):
        self.name = name
        self.free_list = free_list

class ScheduleBot:
    def __init__(self, datadir = DEFAULT_DATA_DIR):
        print('Init new ScheduleBot')
        self.data_dir = datadir
        self.lab_list = self.CreateLabList('lab_list_sp19.csv')
        self.student_list = self.CreateStudentList('master_schedule_sp19.csv')

    def CreateLabList(self,fname):
        lab_list = []
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                lab_list.append(Lab(row[0],int(row[1]),Slot(row[2],row[3],row[4])))
        return lab_list

    def CreateStudentList(self,fname):
        student_list = []
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                print(row)

def CreateSlotList():
    for i in range(SLOT_RANGE):
        day_idx = int(i/(SLOT_RANGE/len(DAYS)))
        hr_idx = int(i%(SLOT_RANGE/len(DAYS)))
        SLOT_LIST.append(Slot(DAYS[day_idx],str(9+hr_idx),str(10+hr_idx)))

if __name__ == '__main__':
    print('Starting scheduling bot')
    CreateSlotList()
    sb = ScheduleBot()
