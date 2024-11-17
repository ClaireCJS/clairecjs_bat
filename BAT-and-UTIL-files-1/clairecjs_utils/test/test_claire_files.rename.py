import os
import fnmatch
import unittest
import claire_files
from colorama import Fore, init
init()

class TestClaireFiles(unittest.TestCase):
    @staticmethod
    def create_test_file(filename):
        with open(filename, 'w') as f: f.write('Test file')

    @staticmethod
    def subtest_announce(subtest):
        #print(f"\t{Fore.LIGHTBLACK_EX}* Test #{subtest}:")
        print(Fore.YELLOW)

    @staticmethod
    def delete_test_files():
        for filename in os.listdir('.'):
            if fnmatch.fnmatch(filename, '*.tst'):
                os.remove(filename)
                assert not os.path.exists(filename), f"{filename} not deleted"

    def setUp(self):
        self.delete_test_files()
        print(Fore.YELLOW, end="")

    def tearDown(self):
        self.delete_test_files()

    def test_claire_rename_function_1(self):
        self.subtest_announce(1)
        self.create_test_file          ('test1.tst' )
        self.assertTrue (os.path.exists('test1.tst'))
        self.assertFalse(os.path.exists('test2.tst'))
        claire_files.rename('test1.tst','test2.tst' )
        self.assertFalse(os.path.exists('test1.tst'))
        self.assertTrue (os.path.exists('test2.tst'))

    def test_claire_rename_function_2(self):
        self.subtest_announce(2)
        self.create_test_file          ('test1.tst'   )      ;  self.assertTrue(os.path.exists('test1.tst'))
        self.create_test_file          ('test2.tst'   )      ;  self.assertTrue(os.path.exists('test2.tst'))
        claire_files.rename('test1.tst','test2.tst'   )
        self.assertTrue(os.path.exists ('test2.tst'  ))
        self.assertTrue(os.path.exists ('test2-1.tst'))      #this should be what it renames test1.tst to if test2.tst already exists

    def test_claire_rename_function_3(self):
        self.subtest_announce(3)
        self.create_test_file          ('test1.tst'  )       ;  self.assertTrue(os.path.exists('test1.tst'  ))
        self.create_test_file          ('test2.tst'  )       ;  self.assertTrue(os.path.exists('test2.tst'  ))
        self.create_test_file          ('test2-1.tst')       ;  self.assertTrue(os.path.exists('test2-1.tst'))
        claire_files.rename('test1.tst','test2.tst'  )
        self.assertTrue(os.path.exists('test2.tst'  ))       #should still be here from initial conditions
        self.assertTrue(os.path.exists('test2-1.tst'))       #should still be here from initial conditions
        self.assertTrue(os.path.exists('test2-2.tst'))       # *** THIS *** should be the newly-named file

if __name__ == '__main__':
    unittest.main()
