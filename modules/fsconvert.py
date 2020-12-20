def padhex(n):
    "Returns hex value in 4 digits: 0x0012 with padded 0"
    return str.format('0x{:04X}', int(hex(n),16))

def vhf_bcd2float(f):
    "Convert vhf frequency in bdc to float"
    freq=(float(padhex(f)[2:6])+10000)/100
    lastDigit=padhex(f)[5:6]
    if (lastDigit=="2" or lastDigit=="7"):
        freq+=0.005
    return freq

def vhf_float2bcd(f):
    "Convert chf freqency in float to bcd"
    v=int("0x"+str(int((f)*100-10000)),16)
    return v

def adf_bcd2float(f1, f2):
    "Convert adf frequency in bcd (fisrt and second offset) to float"
    
    "Force HEX number in 4 digits formated strings"
    f1=padhex(f1)
    f2=padhex(f2)
    
    fmiddle=float(f1[2:6])
    fthausands=float(f2[3:4])*1000
    ftenth=float(f2[5:6])/10
    return fthausands+fmiddle+ftenth

def adf_float2bcd(f):
    "Returns dictionnary of 2 offsets for convertes frequency in bcd"
    if f>999:
        v=int("0x"+str(int(f-1000)),16)
    else:
        v=int("0x"+str(int(f)),16)

    if f>999:
        m=int(f-1000)
        t=1
        c=(f-m-1000)*10
    else:
        t=0
        m=int(f)
        c=(f-m)*10
    return (v,int("0x"+str(int(t*100+c)),16))

def xpdr_bcd2int(f):
    "Returns XPDR code from BCD to float"
    return int(padhex(f)[2:6])

def xpdr_int2bcd(f):
    "Returns XPDR code from float to bcd"
    return int("0x"+str(int(f)),16)

def bearing(f):
    "Returns bearing"
    return f%360
        