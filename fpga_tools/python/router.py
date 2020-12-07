
import modids
import memory


class Router(memory.Memory):
    
    #2x2 star-mesh NoC
    ROUTER_CNT = 4

    #each router has 3 modules, 2 inter-router links, 1 internal link
    ROUTER_LINKCNT = [(modids.MODID_ROUTER[x], 6) for x in range(ROUTER_CNT)]

    def __init__(self, nocif, nocid, router_num):
        self.nocid = nocid
        self.router_num = router_num
        self.shortname = "router"
        self.name = "NoC Router"
        self.mem = memory.Memory(nocif, nocid)

    """
    - number of links per router: module links, inter-router links, internal router link
    - module links are enumerated according to selected z-coordinate of modid
    - inter-router links are enumerated clock-wise beginning at north-link
    """
    def getFlitCountLink(self, link, reset=0):
        if link < self.ROUTER_LINKCNT[self.router_num][1]:
            if reset == 0:
                addr = (0x3<<28) | ((link+8)<<24)
            else:
                addr = (0x4<<28) | ((link+8)<<24)
            return self.mem[addr]
        else:
            return 0

    def getFlitCount(self, reset=0):
        flitCnt = []
        for link in range(self.ROUTER_LINKCNT[self.router_num][1]):
            flitCnt.append(self.getFlitCountLink(link, reset))
        return flitCnt
