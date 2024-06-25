# WintermCrack

WintermCrack is a BIOS password recovery utility for Wyse (now Dell) Winterm SX0 devices that generates a valid password from an EEPROM dump of the Network Interface Controller.

WintermCrack has been tested with:
* Wyse Winterm SX0 S30

If you tested this application with any other Winterm model, please report your success or failure in order to keep this list up to date.

Please note, this tool requires you to take apart the device, connect an external programmer, maybe even de-solder and re-solder an SMD chip. It ain't rocket surgery, but please be careful and use your brain. I am not responsible for any damage you may cause to yourself or the device.

## Requirements and Pre-requisites

You will need a reasonably new Python 3 version, which can be easily acquired [python.org](https://www.python.org/) or from repository of your distribution.

WintermCrack does not have any OS dependencies, so it should work on any OS that supports Python 3.

In order to generate a valid BIOS password, you will also need an EEPROM dump of the RTL8100CL network interface controller. I

## Acquiring EEPROM dump

The password hash is stored in the EEPROM of the RTL8100CL. The EEPROM is an Atmel AT93C46, whose location is shown in the image below:

![winterm_sx0_S30_eeprom](https://github.com/TeisybeLT/WintermCrack/assets/35064004/90bef4fb-5bb6-46b7-9431-a84b2abe58b2)

There are many off the shelf dumpers capable of dumping this EEPROM, such as:
* XGecu T45/T58 or similar
* CH341-based programmers (please note, a voltage mod may be required for these programmers)
* XP866+ programmer

In a pinch, you can build a programmer using some common components, such as:
* Raspberry Pi Pico + [pico-serprog](https://github.com/stacksmashing/pico-serprog)
* Raspberry Pi + flashrom
* Ardunino (please be mindful of voltages)

Irregardless of which programmer/dumper you choose, connect it to the IC and acquire a dump of it. The exact process for dumping will depend on which programmer you choose. It should be 128 bytes. I suggest making multiple dumps and compare their checksum to ensure that the dump is correct.

I also had to de-solder the IC, because other things are connected to the Vcc line, thus drawing too much current from the programmer and tripping the over-current protection mechanism of the programmer.

## Using WintermCrack

1. Download or clone this repository
2. Open terminal and navigate to a directory containing files from this repository
3. Executed the script, supplying the path to the EEPROM dump as such:
```
./wintermcrack.py <path to dump>
```
or
```python
python wintermcrack.py <path to dump>
```
4. The generated password will be printed in the terminal

If you encounter any issues, please raise an issue in this GitHub repository.

## Theory of operation

The BIOS password of the Wyse Winterm SX0 uses a very weak hash (if you can even call it that), which just sums ASCII values of each character in the password string and stores the lower byte into EEPROM (discarding all the data in the upper bytes). The length of the password is also stored in the EEPROM alongside the hash value. Given this information, generating a string of a given length which causes a collision is trivial.

In my implementation of the password generator, I am generating a random string with the length of _n-1_, where _n_ is the password length retrieved from EEPROM. Then I compute the last character by taking the absolute value of the difference between lower byte of the sum of all generated characters and the hash value retrieved from memory. If the computed value is not printable - I retry the generation algorithm until a printable character is found. It usually takes less than 5 iterations to produce a valid password.