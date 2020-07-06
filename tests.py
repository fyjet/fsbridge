import unittest
import fsconvert

class TestFSConvert(unittest.TestCase):
    
    def test_padhex(self):
        self.assertEqual(fsconvert.padhex(0xA),'0x000A')
        self.assertEqual(fsconvert.padhex(0x1234),'0x1234')
        self.assertEqual(fsconvert.padhex(0x90),'0x0090')
        
    def test_adf_bcd2float(self):
        self.assertEqual(fsconvert.adf_bcd2float(0x0234,0x0105),1234.5)
        self.assertEqual(fsconvert.adf_bcd2float(0x234,0x105),1234.5)
        self.assertEqual(fsconvert.adf_bcd2float(0x34,0x105),1034.5)
        self.assertEqual(fsconvert.adf_bcd2float(0x234,0x5),234.5)
    
    def test_adf_float2bcd(self):
        self.assertEqual(fsconvert.padhex(fsconvert.adf_float2bcd(1234.5)[0]),'0x0234')
        self.assertEqual(fsconvert.padhex(fsconvert.adf_float2bcd(1234.5)[1]),'0x0105')
    
    def test_vhf_float2bcd(self):
        self.assertEqual(fsconvert.padhex(fsconvert.vhf_float2bcd(123.45)),'0x2345')
        self.assertEqual(fsconvert.padhex(fsconvert.vhf_float2bcd(113.45)),'0x1345')
    
    def test_vhf_bcd2float(self):
        self.assertEqual(fsconvert.vhf_bcd2float(0x2345),123.45)
        self.assertEqual(fsconvert.vhf_bcd2float(0x1345),113.45)
        self.assertEqual(fsconvert.vhf_bcd2float(0x345),103.45)
    
    def test_xpdr_bcd2int(self):
        self.assertEqual(fsconvert.xpdr_bcd2int(0x1200),1200)
        
    def test_xpdr_int2bcd(self):
        self.assertEqual(fsconvert.padhex(fsconvert.xpdr_int2bcd(1200)),'0x1200')
        
if __name__ == '__main__':
    unittest.main()