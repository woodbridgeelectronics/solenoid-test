# readme

Setup instruction
   1. connect Solenoid Control Board to a Windows PC
   2. download USB device driver.zip and install USB device driver
   3. download LMFlashProgrammer_1613.msi and flash project.bin to the connected Solenoid Control Board
   4. download setup_solenoid_test.exe, install and run solenoid test program




USB device driver.zip:         Windows device driver for Solenoid Control Board
   
setup_solenoid_test.exe:       installation file for the Solenoid Test program

LMFlashProgrammer_1613.msi:    setup file for LM Flash Programmer. This utility is used to upgrade the firmware on Solenoid Control Board

project.bin:                   firmware binary file on Solenoid Control Board. this file can be downloaded with LM Flash Programmer utility.

project.zip:                  firmware source code. firmware is developed with TI Source Composer Studio 6.2.0

solenoid_test.py:              sourcecode file. The software was developed under Python 2.7.10 64-bit and wxPython 3.0 environment. The sourcecode can run directly with environment setup properly. The sourcecode was converted to Windows executable with pyinstall tool. Windows executable files were packaged into single setup file with Inno setup 5 software.

