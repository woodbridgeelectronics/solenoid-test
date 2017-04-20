# readme

Setup instruction
   1. connect Solenoid Control Board to a Windows PC
   2. download USB device driver.zip and install USB device driver
   3. download LMFlashProgrammer_1613.msi and flash project.bin to the connected Solenoid Control Board
   4. download setup_solenoid_test.exe, install and run solenoid test program




USB device driver.zip 
   this file contains the Windows device driver for Solenoid Control Board
   
setup_solenoid_test.exe 
   this file is the installation file for the Solenoid Test program

LMFlashProgrammer_1613.msi
   this file is the setup file for LM Flash Programmer. This utility is used to upgrade the firmware on Solenoid Control Board

project.bin
   this is the firmware binary file on Solenoid Control Board. this file can be downloaded with LM Flash Programmer utility.
   
solenoid_test.py 
   this is the sourcecode file. The software was developed under Python 2.7.10 64-bit and wxPython 3.0 environment. The sourcecode can run directly with environment setup properly. The sourcecode was converted to Windows executable with pyinstall tool. Windows executable files were packaged into single setup file with Inno setup 5 software.
