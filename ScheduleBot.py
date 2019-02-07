import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import csv, time

DEFAULT_DATA_DIR = './Data/'
DAYS = ['M','T','W','R','F']
TA_SLOT_RANGE = 65
TA_SLOT_LIST = []

class Slot:
    def __init__(self,day,start,end):
        self.day = day
        self.start = start
        self.end = end

    def PrintSlot(self):
        print(self.day, self.start, self.end)

    def __eq__(self,other):
        if isinstance(other, Slot):
            return self.day==other.day and self.start==other.start and self.end==other.end
        return NotImplemented

    def __hash__(self):
        return hash((self.day,self.start,self.end))

class Lab:
    def __init__(self,type,section,slot,TA=''):
        self.type = type
        self.section = section
        self.slot = slot
        self.TA = TA

    def PrintLab(self):
        print(('%s, %d, %s, %s, %s, %s')%(self.type,self.section,self.slot.day,self.slot.start,self.slot.end,self.TA.name))

class Test:
    def __init__(self, class_n, prof, date, slot, n_students):
        self.class_num = class_n
        self.professor = prof
        self.date = date
        self.slot = slot
        self.num_students = n_students
        self.TAs = []

class TA:
    def __init__(self,name,free_list,has_lab=False, proctor=0, grade=0):
        self.name = name
        self.free_list = free_list
        self.has_lab = has_lab
        self.restrictivity = len(free_list)
        self.proctor = proctor
        self.grade = grade

    def CheckFreeList(self,slot):
        return all(elem in self.free_list for elem in LAB_SLOT_TO_TA_SLOT_DICT[slot])

class ScheduleBot:
    def __init__(self, lab_fname, TA_fname, test_fname, tally_fname, datadir = DEFAULT_DATA_DIR):
        print('\nScheduleBot Initialized')
        self.data_dir = datadir
        self.lab_list = self.CreateLabList(lab_fname)
        self.TA_hash = self.CreateTAHash(tally_fname)
        self.TA_list = self.CreateTAList(TA_fname)
        self.test_list = self.CreateTestList(test_fname)

    def CreateLabList(self,fname):
        lab_list = []
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                lab_list.append(Lab(row[0],int(row[1]),Slot(row[2],row[3],row[4])))
        return lab_list

    def CreateTAList(self,fname):
        TA_list = []
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            i=0
            for row in reader:
                free_list = []
                name = row.pop(0)
                for j in range(len(row)):
                    if 'OK' not in row[j]:
                        free_list.append(j)
                TA_list.append(TA(name,free_list, proctor=self.TA_hash[name]['proctor'], grade=self.TA_hash[name]['grade']))
        return TA_list

    def CreateTestList(self,fname):
        test_list = []
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                class_n = row[0]
                prof = row[1]
                slot = Slot(row[2],row[3].split(', ')[1].split('-')[0], row[3].split(', ')[1].split('-')[1])
                date = row[3].split(', ')[0]
                n_students = int(row[4])
                test_list.append(Test(class_n,prof,slot,date,n_students))
        return test_list

    def CreateTAHash(self,fname):
        TA_hash = {}
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                name = row[0]
                proctor = int(row[2])+int(row[4])+int(row[6])+int(row[8])
                grade = int(row[3])+int(row[5])+int(row[7])+int(row[9])
                TA_hash[name] = {'proctor':proctor,'grade':grade}
        print(TA_hash)
        return TA_hash

    def ScheduleLabs(self):
        for lab in self.lab_list:
            min_restrictivity = 100
            lab_slot = lab.slot
            lab_TA = TA('',[])
            for ta in self.TA_list:
                if ta.CheckFreeList(lab_slot) and ta.restrictivity < min_restrictivity and not ta.has_lab:
                    min_restrictivity = ta.restrictivity
                    lab_TA = ta
            lab.TA = lab_TA
            lab_TA.has_lab = True

    def PrintAllLabs(self):
        for lab in self.lab_list:
            lab.PrintLab()

def CreateStudentSlotList():
    for i in range(TA_SLOT_RANGE):
        day_idx = int(i/(TA_SLOT_RANGE/len(DAYS)))
        hr_idx = int(i%(TA_SLOT_RANGE/len(DAYS)))
        TA_SLOT_LIST.append(Slot(DAYS[day_idx],str(9+hr_idx),str(10+hr_idx)))

LAB_SLOT_TO_TA_SLOT_DICT = {
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

TEST_SLOT_TO_TA_SLOT_DICT = {
    Slot('M', '10:10', '11:25'): [1,2],
    Slot('M', '11:40', '12:55'): [2,3],
    Slot('M', '13:10', '14:25'): [4,5],
    Slot('M', '14:40', '15:55'): [5,6],
    Slot('M', '18:10', '19:25'): [9,10],
    Slot('T', '10:10', '11:25'): [14,15],
    Slot('T', '11:40', '12:55'): [15,16],
    Slot('T', '13:10', '14:25'): [17,18],
    Slot('T', '14:40', '15:55'): [18,19],
    Slot('T', '18:10', '19:25'): [22,23],
    Slot('W', '10:10', '11:25'): [27,28],
    Slot('W', '11:40', '12:55'): [28,29],
    Slot('W', '13:10', '14:25'): [30,31],
    Slot('W', '14:40', '15:55'): [31,32],
    Slot('W', '18:10', '19:25'): [35,36],
    Slot('R', '10:10', '11:25'): [40,41],
    Slot('R', '11:40', '12:55'): [41,42],
    Slot('R', '13:10', '14:25'): [43,44],
    Slot('R', '14:40', '15:55'): [44,45],
    Slot('R', '18:10', '19:25'): [48,49],
    Slot('F', '10:10', '11:25'): [53,54],
    Slot('F', '11:40', '12:55'): [54,55],
    Slot('F', '13:10', '14:25'): [56,57],
    Slot('F', '14:40', '15:55'): [57,58],
    Slot('F', '18:10', '19:25'): [61,62],
}

if __name__ == '__main__':
    print('\nStarting scheduling process')
    CreateStudentSlotList()
    sb = ScheduleBot('lab_list_sp19.csv','master_schedule_sp19.csv', 'proctor_grading_list_sp19.csv', 'proctor_grading_tally.csv')
    #sb.ScheduleLabs()
    #sb.PrintAllLabs()
    print('\nScheduling process finished')
