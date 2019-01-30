import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import csv, time

DEFAULT_DATA_DIR = './Data/'
DAYS = ['M','T','W','R','F']
STUDENT_SLOT_RANGE = 65
STUDENT_SLOT_LIST = []

class Slot:
    def __init__(self,day,start,end):
        self.day = day
        self.start = start
        self.end = end

    def __eq__(self,other):
        if isinstance(other, Slot):
            return self.day==other.day and self.start==other.start and self.end==other.end
        return NotImplemented

    def __hash__(self):
        return hash((self.day,self.start,self.end))

class Lab:
    def __init__(self,type,section,slot,student=''):
        self.type = type
        self.section = section
        self.slot = slot
        self.student = student

    def PrintLab(self):
        print(('%s, %d, %s, %s, %s, %s')%(self.type,self.section,self.slot.day,self.slot.start,self.slot.end,self.student.name))

class Student:
    def __init__(self,name,free_list,has_lab=False):
        self.name = name
        self.free_list = free_list
        self.has_lab = has_lab
        self.restrictivity = len(free_list)

    def CheckFreeList(self,slot):
        return all(elem in self.free_list for elem in LAB_SLOT_TO_STUDENT_SLOT_DICT[slot])

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
            i=0
            for row in reader:
                free_list = []
                name = row.pop(0)
                for j in range(len(row)):
                    if 'OK' not in row[j]:
                        free_list.append(j)
                student_list.append(Student(name,free_list))
        return student_list

    def Schedule(self):
        for lab in self.lab_list:
            min_restrictivity = 100
            lab_slot = lab.slot
            lab_student = Student('',[])
            for student in self.student_list:
                if student.CheckFreeList(lab_slot) and student.restrictivity < min_restrictivity and not student.has_lab:
                    min_restrictivity = student.restrictivity
                    lab_student = student
            lab.student = lab_student
            lab_student.has_lab = True

    def PrintAllLabs(self):
        for lab in self.lab_list:
            lab.PrintLab()

def CreateStudentSlotList():
    for i in range(STUDENT_SLOT_RANGE):
        day_idx = int(i/(STUDENT_SLOT_RANGE/len(DAYS)))
        hr_idx = int(i%(STUDENT_SLOT_RANGE/len(DAYS)))
        STUDENT_SLOT_LIST.append(Slot(DAYS[day_idx],str(9+hr_idx),str(10+hr_idx)))

LAB_SLOT_TO_STUDENT_SLOT_DICT = {
    Slot('M','13:00','16:00'): [4,5,6],
    Slot('M','16:10','19:10'): [7,8,9,10],
    Slot('M','19:30','22:30'): [10,11,12],
    Slot('T','13:00','16:00'): [17,18,19],
    Slot('T','16:10','19:10'): [20,21,22,23],
    Slot('T','19:30','22:30'): [23,24,25],
    Slot('W','13:00','16:00'): [30,31,32],
    Slot('W','16:10','19:10'): [33,34,35,36],
    Slot('W','19:30','22:30'): [36,37,38],
    Slot('R','13:00','16:00'): [43,44,45],
    Slot('R','16:10','19:10'): [46,47,48,49],
    Slot('R','19:30','22:30'): [49,50,51],
    Slot('F','13:00','16:00'): [56,57,58],
    Slot('F','16:10','19:10'): [59,60,61,62],
    Slot('F','19:30','22:30'): [62,63,64],
}

if __name__ == '__main__':
    print('Starting scheduling bot')
    CreateStudentSlotList()
    sb = ScheduleBot()
    sb.Schedule()
    sb.PrintAllLabs()
