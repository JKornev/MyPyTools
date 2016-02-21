import sys, re
from pykd import *

'''
TODO:
+ support x64
- support different breakpoints
+ remove temporary breakpoints
- recursion decrease
- args output (optional)
'''

g_is_x64 = False

def init_script():
    global g_is_x64

    dprintln("============================================================")
    
    if not isWindbgExt():
        dprintln("Spoof-API doesn't run under windbg")
        exit()
        
    try:
        r = reg("rip")
        g_is_x64 = True
    except:
        pass
    
    dprintln("Spoof-API is running under " + ("x64" if g_is_x64 else "x86"))
    

def get_reg(base):#TODO:
    return reg(("r" if g_is_x64 else "e") + base)


def trace_api(moduleName, mask = "*"):

    mod = module( moduleName )
    dprintln("Module: " + moduleName + ", base: %x" % mod.begin() + ", end: %x" % mod.end())

    # set breakpoints to specific module with mask
    res = dbgCommand("bm " + moduleName + "!" + mask)
    dprint(res)

    # find all our breakpoint IDs
    bp_ids = re.findall("\s*(\d+)\:\s*", res, re.M)

    try:
        while True:
            go()

            try:
                res = mod.findSymbolAndDisp(get_reg("ip"))
                #TODO: catch invalid address for compatibility with other breakpoints
            except Exception as e:
                print e
                break
            
            dprintln("[API] %x %s" % (get_reg("ip"), res[0]))
            
    finally:
        # remove our breakpoints
        for elem in bp_ids:
            dbgCommand("bc " + elem)
            
    
        
if __name__ == "__main__":

    init_script()
    
    if len(sys.argv)<=1:
        dprintln("usage: !py apitrace <module> [symbol pattern]")
    elif len(sys.argv) == 2:
        trace_api(sys.argv[1])
    else:
        trace_api(sys.argv[1], sys.argv[2])
