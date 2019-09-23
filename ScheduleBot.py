import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import csv, time, sys
from random import shuffle

DEFAULT_DATA_DIR = './Data/'
DAYS = ['M','T','W','R','F']
TA_SLOT_RANGE = 65
TA_SLOT_LIST = []

# Class for time slots (day, start time (24 hr clock), end time (24 hr clock))
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

# Class for labs (lab_type, section number, slot, assigned TA)
class Lab:
    def __init__(self,lab_type,section,slot,TA=''):
        self.lab_type = lab_type
        self.section = section
        self.slot = slot
        self.TA = TA

    def PrintLab(self):
        print(('%s, %d, %s, %s, %s, %s')%(self.lab_type,self.section,self.slot.day,self.slot.start,self.slot.end,self.TA.name))

# Class for tests (class number, professor name, date of test, slot, number of students)
class Test:
    def __init__(self, class_n, prof, date, slot, n_students):
        self.class_num = class_n
        self.professor = prof
        self.date = date
        self.slot = slot
        self.num_students = n_students
        self.num_proctors = int(2+n_students/100)
        self.num_graders = int(min(3+n_students/60,5))
        self.proctors = []
        self.graders = []

    def PrintTest(self):
        print(("%d, %s, %s\n\t%s\n\t%s")%(self.class_num,self.professor,self.date,str(self.proctors),str(self.graders)))

# Class for TAs (namer of TA, list of free times, has lab boolean, number of times proctored, number of times graded)
class TA:
    def __init__(self,name,free_list,has_lab=False, proctor=0, grade=0, total_num_students=0):
        self.name = name
        self.free_list = free_list
        self.has_lab = has_lab
        self.restrictivity = len(free_list)
        self.proctor = proctor
        self.grade = grade
        self.total_num_students = total_num_students

    def CheckFreeList(self,slot,lab_or_test,midterm=False):
        if midterm:
            slot_dict = (LAB_SLOT_TO_TA_SLOT_DICT, MIDTERM_SLOT_TO_TA_SLOT_DICT)[lab_or_test=='test']
        else:
            slot_dict = (LAB_SLOT_TO_TA_SLOT_DICT, FINAL_SLOT_TO_TA_SLOT_DICT)[lab_or_test=='test']
        return all(elem in self.free_list for elem in slot_dict[slot])

    def GetAvgStudentsGraded(self):
        if self.grade!=0:
            return round(self.total_num_students/self.grade,1)
        else:
            return 0

    def __repr__(self):
        return self.name

# Class for ScheduleBot, the bot that does the scheduling (filename for list of labs, filename for list of TA availability, filename for tests, filename for proctor/grade tally sheet)
class ScheduleBot:
    def __init__(self, lab_fname, TA_fname, test_fname, tally_fname, datadir = DEFAULT_DATA_DIR):
        print('\nScheduleBot Initialized')
        self.data_dir = datadir
        self.lab_list = self.CreateLabList(lab_fname)
        self.TA_hash = self.CreateTAHash(tally_fname)
        self.TA_list = self.CreateTAList(TA_fname)
        self.test_list = self.CreateTestList(test_fname)

    # Creators
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
                    if row[j]=='':
                        free_list.append(j)
                TA_list.append(TA(name,free_list, proctor=self.TA_hash[name]['proctor'], grade=self.TA_hash[name]['grade'], total_num_students=self.TA_hash[name]['total_num_students']))
        return TA_list

    def CreateTestList(self,fname):
        test_list = []
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                class_n = int(row[0])
                prof = row[1]
                slot = Slot(row[2],row[3].split(', ')[1].split('-')[0], row[3].split(', ')[1].split('-')[1])
                date = row[3].split(', ')[0]
                n_students = int(row[4])
                test_list.append(Test(class_n,prof,date,slot,n_students))
        return test_list

    def CreateTAHash(self,fname):
        TA_hash = {}
        with open(self.data_dir+fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                name = row[0]
                proctor,grade,num_students=0,0,0
                for i in range(4):
                    proctor += int(row[2+3*i])
                    grade += int(row[3+3*i])
                    num_students += int(row[4+3*i])
                TA_hash[name] = {'proctor':proctor,'grade':grade,'total_num_students':num_students}
        return TA_hash

    # Getters
    def GetAvgStudentsGraded(self):
        return round(np.mean([ta.GetAvgStudentsGraded() for ta in self.TA_list]),2)

    def GetStdStudentsGraded(self):
        return round(np.std([ta.GetAvgStudentsGraded() for ta in self.TA_list]),2)

    def GetAvgTestsGraded(self):
        return round(np.mean([ta.total_num_students for ta in self.TA_list]),2)

    def GetStdTestsGraded(self):
        return round(np.std([ta.total_num_students for ta in self.TA_list]),2)

    # Schedulers
    def ScheduleLabs(self):
        for lab in self.lab_list:
            min_restrictivity = 100
            lab_slot = lab.slot
            lab_TA = TA('',[])
            for ta in self.TA_list:
                if ta.CheckFreeList(lab_slot,'lab') and ta.restrictivity < min_restrictivity and not ta.has_lab:
                    min_restrictivity = ta.restrictivity
                    lab_TA = ta
            lab.TA = lab_TA
            lab_TA.has_lab = True

    def ScheduleTests(self,midterm=False):
        for test in self.test_list:
            test_slot = test.slot
            test_num_students = test.num_students
            for n in range(test.num_proctors):
                proctor = TA('',[])
                min_proctor_restrictivity = 100
                #shuffle(self.TA_list)
                for ta in self.TA_list:
                    if ta.CheckFreeList(test_slot,'test',midterm) and ta.proctor < min_proctor_restrictivity and ta not in test.proctors:
                        proctor = ta
                        min_proctor_restrictivity = ta.proctor
                test.proctors.append(proctor)
                proctor.proctor+=1
            for n in range(test.num_graders):
                grader = TA('',[])
                min_std = 1000
                for ta in self.TA_list:
                    ta.grade +=1
                    ta.total_num_students += test_num_students
                    curr_std = self.GetStdTestsGraded()
                    if curr_std < min_std and ta not in test.graders:
                        grader = ta
                        min_std = curr_std
                    ta.grade-=1
                    ta.total_num_students -= test_num_students
                test.graders.append(grader)
                grader.grade+=1
                grader.total_num_students += test_num_students

    # Writers
    def WriteTestSchedule(self,sched_fname):
        with open(DEFAULT_DATA_DIR+sched_fname, mode='w+') as pgfile:
            pgwriter = csv.writer(pgfile, delimiter=',')
            pgwriter.writerow(['Class Number','Section Number','Midterm Date', 'Proctors','','','','Graders','','','',''])
            for test in self.test_list:
                row = [test.class_num,test.professor,test.date]+test.proctors+['']*(4-len(test.proctors))+test.graders
                pgwriter.writerow(row)

    def WriteLabSchedule(self):
        with open(DEFAULT_DATA_DIR+'lab_schedule_sp19.csv', mode='w+') as labfile:
            labwriter = csv.writer(labfile, delimiter=',')
            labwriter.writerow(['Lab Type','Section Number','TA'])
            for lab in self.lab_list:
                row = [lab.lab_type,lab.section,lab.TA.name]
                labwriter.writerow(row)

    # Printers
    def PrintAllLabs(self):
        for lab in self.lab_list:
            lab.PrintLab()

    def PrintAllTests(self):
        for test in self.test_list:
            test.PrintTest()

    def PrintAllTAs(self, this_sem=False):
        for ta in self.TA_list:
            proctor_this_sem = ta.proctor-self.TA_hash[ta.name]['proctor']
            grade_this_sem = ta.grade-self.TA_hash[ta.name]['grade']
            if this_sem:
                print(ta.name,proctor_this_sem,grade_this_sem,ta.total_num_students,ta.GetAvgStudentsGraded())
            else:
                print(ta.name,ta.proctor,ta.grade,ta.total_num_students,ta.GetAvgStudentsGraded())

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

MIDTERM_SLOT_TO_TA_SLOT_DICT = {
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

FINAL_SLOT_TO_TA_SLOT_DICT = {
    Slot('M', '9:00', '12:00'): [0,1,2],
    Slot('M', '13:10', '16:00'): [4,5,6],
    Slot('M', '16:10', '19:00'): [7,8,9],
    Slot('M', '19:10', '22:00'): [10,11,12],
    Slot('T', '9:00', '12:00'): [13,14,15],
    Slot('T', '13:10', '16:00'): [17,18,19],
    Slot('T', '16:10', '19:00'): [20,21,22],
    Slot('T', '19:10', '22:00'): [23,24,25],
    Slot('W', '9:00', '12:00'): [26,27,28],
    Slot('W', '13:10', '16:00'): [30,31,32],
    Slot('W', '16:10', '19:00'): [33,34,35],
    Slot('W', '19:10', '22:00'): [36,37,38],
    Slot('R', '9:00', '12:00'): [39,40,41],
    Slot('R', '13:10', '16:00'): [43,44,45],
    Slot('R', '16:10', '19:00'): [46,47,48],
    Slot('R', '19:10', '22:00'): [49,50,51],
    Slot('F', '9:00', '12:00'): [52,53,54],
    Slot('F', '13:10', '16:00'): [56,57,58],
    Slot('F', '16:10', '19:00'): [59,60,61],
    Slot('F', '19:10', '22:00'): [62,63,64]
}

if __name__ == '__main__':
    print('\nStarting scheduling process\n')
    lab_fname,TA_fname,test_fname,tally_fname = ['']*4
    CreateStudentSlotList()
    if len(sys.argv)==2  and sys.argv[1] == 'midterm':
        lab_fname = 'lab_list_sp19.csv'
        TA_fname = 'master_schedule_sp19.csv'
        test_fname = 'midterm_list_sp19.csv'
        sched_fname = 'midterm_schedule_sp19.csv'
        tally_fname = 'proctor_grading_tally_num_students_sp19.csv'
    elif len(sys.argv)==2  and sys.argv[1] == 'final':
        lab_fname = 'lab_list_sp19.csv'
        TA_fname = 'master_schedule_sp19.csv'
        test_fname = 'final_list_sp19.csv'
        sched_fname = 'final_schedule_sp19.csv'
        tally_fname = 'proctor_grading_tally_num_students_sp19.csv'
    else:
        lab_fname = input('Please enter filename for lab list:')
        TA_fname = input('Please enter filename for TA master schedule:')
        test_fname = input('Please enter filename for test list:')
        tally_fname = input('Please enter filename for tally list:')
    sb = ScheduleBot(lab_fname,TA_fname,test_fname,tally_fname)
    #sb.ScheduleLabs()
    #sb.WriteLabSchedule()
    sb.ScheduleTests(midterm=False)
    sb.WriteTestSchedule(sched_fname)
    sb.PrintAllTAs(this_sem=True)
    print()
    print(sb.GetAvgTestsGraded())
    print(sb.GetStdTestsGraded())
    print('\nScheduling process finished')
