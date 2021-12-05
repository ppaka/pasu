import maploader

class Notemanager:
    keypositions = None
    notelist = None

    k1list = []
    k2list = []
    k3list = []
    k4list = []

    def Setup(self, beatmap):
        self.keypositions = maploader.Maploader().load_keyposition(beatmap)
        self.notelist = maploader.Maploader().load_notes(beatmap, self.keypositions)
        self.k1list = []
        self.k2list = []
        self.k3list = []
        self.k4list = []

    def SpawnNote(self, gametime, duration):
        # gametime 이 [생성전 대기중인 노트리스트] 0번의 스폰시간을 넘었으면
        if len(self.notelist) != 0:
            if gametime >= self.notelist[0].starttime - duration:
                if len(self.notelist) == 1:
                    self.notelist[0].islastNote = True
                if self.notelist[0].key == 0:
                    self.k1list.append(self.notelist.pop(0))  # 해당하는 키 리스트에 넣는다
                elif self.notelist[0].key == 1:
                    self.k2list.append(self.notelist.pop(0))
                elif self.notelist[0].key == 2:
                    self.k3list.append(self.notelist.pop(0))
                elif self.notelist[0].key == 3:
                    self.k4list.append(self.notelist.pop(0))
    def CheckMiss(self, i, gametime):
        # if i.notetype == 1 and gametime > i.endtime + 124.5: # 롱노트 일때
        #     # print("MISS / ", gametime - i.starttime)
        #     if i.key == 0:
        #         self.k1list.remove(i)
        #     elif i.key == 1:
        #         self.k2list.remove(i)
        #     elif i.key == 2:
        #         self.k3list.remove(i)
        #     elif i.key == 3:
        #         self.k4list.remove(i)
        #     return True
        if i.notetype == 0 and gametime > i.starttime + 124.5: # 일반노트 일때
            # print("MISS / ", gametime - i.starttime)
            if i.key == 0:
                self.k1list.remove(i)
            elif i.key == 1:
                self.k2list.remove(i)
            elif i.key == 2:
                self.k3list.remove(i)
            elif i.key == 3:
                self.k4list.remove(i)
            return True
        else: 
            return False