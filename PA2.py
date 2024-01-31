import sys
import struct

unique_registers = { 28:"SP", 29:"FP", 30: "LR", 31:"XZR" }
instruction = []
listbinary = []
labels = {}
labelnum = 1 #iterate for ea new label
# r type; rm is 5 bits wide, rn is 5 bits wide, 
# rd is 5 bits wide
# shamt is 6 bits wide
# opcode is 11 bits 
# opcode, Rm, Shamt, Rn, Rd
# would it be easier to type out hmmm

# PRNT: This is an added instruction (part of our emulator, but not part of LEG or ARM) that prints a register name 
# and its contents in hex and decimal.  This is an R instruction.  The opcode is 11111111101.  The register is given in the Rd field.

# PRNL: This is an added instruction that prints a blank line.  This is an R instruction.  The opcode is 11111111100.

# DUMP: This is an added instruction that displays the contents of all registers and memory, as well as the disassembled program.  
# This is an R instruction.  The opcode is 11111111110.

# HALT: This is an added instruction that triggers a DUMP and terminates the emulator.  This is an R instruction.  
# The opcode is 11111111111

def rtype(opcode, binary, i): 
    rm = int(binary[0:5],2) # base 2
    shamt = int(binary[5:11], 2)
    rn = int(binary[11:16], 2)
    rd = int(binary[16:21], 2)

    if rm not in unique_registers.keys():
        rm = "X" + str(rm)
    else:
        rm = unique_registers[rm]
    
    if rn not in unique_registers.keys():
        rn = "X" + str(rn) +", "
    else:
        rn = unique_registers[rn] + ", "
    
    if rd not in unique_registers.keys():
        rd = "X" + str(rd) + ", "
    else:
        rd = unique_registers[rd] + ", "
    
    if shamt != 0:
        shamt = "#" + str(shamt) 
    else:
        shamt = ""
    
    # check opcode
    if opcode != "DUMP" and opcode != "HALT" and opcode != "PRNL" and opcode != "PRNT" and opcode != "LSL" and opcode != "LSR":
        rm = rm
    else:
        rm = ""
    
    if opcode != "DUMP" and opcode != "HALT" and opcode != "PRNL" and opcode != "PRNT":
        rn = rn
    else:
        rn = ""
    
    if opcode != "DUMP" and opcode != "HALT" and opcode != "PRNL":
        rd = rd
    else:
        rd = ""
    
    # account for PRNT
    if opcode != "PRNT":
        rd = rd
    else:
        if rd not in unique_registers.keys():
            rd = "X" + str(rd) 
        else:
            rd = unique_registers[rd] 
    instruct = opcode + " " + rd + rn + rm + shamt
    return instruct

def twoscomp(b_addr, length):
    x = b_addr ^ (pow(2, (length+1)) -1)
    x = bin(x +1)[3:]
    b_addr = -1 * int(x, 2)
    return b_addr


#ldur - stur
def dtype(opcode, binary, i):
    rn = int(binary[11:16],2)
    rt = int(binary[16:21], 2)
    if rn not in unique_registers.keys():
        rn = "[X" + str(rn) + ", "
    else:
        rn = "[" + unique_registers[rn] + ", "
    if rt not in unique_registers.keys():
        rt = "[x" + str(rt) + ", "
    else:
        rt = "[" + unique_registers[rt] + ", "
    # off set
    dt_addressn = int(binary[0:9], 2)
    dt_address = "#" + str(dt_address) + "]"
    
    output = opcode + " " + rt + rn + dt_address

    return output

def btype(opcode,binary, i):
    branchlabel = None
    global labelnum
    branchaddress = int(binary, 2)
    if branchaddress > len(instruction):
        branchaddress = twoscomp(branchaddress, len(binary))
    if branchaddress > len(instruction) or branchaddress < -len(instruction):
        label = "LR"

    if not label:
        if (i + branchaddress) in labels.keys():
            label = labels[i + branchaddress]
        else:
            label = "label" + str(labelnum)
            labelnum = labelnum + 1
            labels[i + branchaddress] = label
    output = opcode + " " + label
    return output

def itype(opcode, binary, i):
    rn = int(binary[12:17], 2)
    rd = int(binary[17:22],2 )
    immed = int(binary[0:12], 2)

    immed = "#" + str(immed) # adds the # symbol for ASM
    if rn in unique_registers:
        rn = unique_registers[rn] + ", "
    else:
        rn = "X" + str(rn) + ", "

    if rd in unique_registers:
        rd = unique_registers[rd] + ", "
    else:
        rd = "X" + str(rd) + ", "

    output = opcode + " " + rd + rn +immed
    return output

def cbtype(opcode,binary,i):
    global labelnum
    
    rt = int(binary[19:24], 2)
    
    cb_addr = int(binary[0:19], 2)
    if cb_addr > len(instruction):
        cb_addr = twoscomp(cb_addr, 19) #19 length
    
    if(i + cb_addr) in labels.keys():
        label = labels[i + cb_addr]
    else:
        label = "label" + str(labelnum)
        labels[i +cb_addr] = label


        labelnum = labelnum+1
    
    if opcode == "B.cond":
        output = "B." + bcond[rt] + " " + label
    else:
        output = opcode + " X" + str(rt) + ", " + label
    
    return output
        




bcond = {
    '0':"EQ",
    '1':"NE",
    '2':"HS",
    '3':"LO",
    '4':"MI",
    '5':"PL",
    '6':"Vs",
    '7':"VC",
    '8':"HI",
    '9':"LS",
    'a':"GE",
    'b':"LT",
    'c':"GT",
    'd':"LE"
}

# key value pairs for ops
ops = {
    '0b10001011000':["ADD", rtype],
    '0b1001000100' :["ADDI", itype],
    '0b10001010000':["AND", rtype],
    '0b1001001000' :["ANDI", itype],
    '0b000101'     :["B", btype],
    '0b100101'     :["BL", btype],
    '0b01010100'   :["B.cond", cbtype],
    '0b11010110000':["BR", btype],
    '0b10110101'   :["CBNZ", cbtype],
    '0b10110100'   :["CB", cbtype],
    '0b11111111110':["DUMP", rtype],
    '0b11001010000':["EOR", rtype],
    '0b1101001000' :["EORI", itype],
    '0b11111111111':["HALT", rtype],
    '0b11111000010':["LDUR", dtype],
    '0b11010011011':["LSL", rtype],
    '0b11010011010':["LSR", rtype],
    '0b10011011000':["MUL", rtype],
    '0b10101010000':["ORR", rtype],
    '0b1011001000' :["ORRI", itype],
    '0b11111111100':["PRNL", rtype],
    '0b11111111101':["PRNT", rtype],
    '0b11111000000':["STUR", dtype],
    '0b11001011000':["SUB", rtype],
    '0b1101000100' :["SUBI", itype],
    '0b1111000100' :["SUBIS", itype],
    '0b11101011000':["SUBS", rtype]

}






try:
    if ".machine" not in sys.argv[1]:
        print("File must be .machine type")
        exit(1)

    with open( sys.argv[1], 'rb' ) as file:
        
        while True:
            buff = file.read(4)
            if buff:
                x = struct.unpack('>I', buff)[0] # for big endian
                listbinary.append(bin(x))
            else:
                break
    file.close()

except FileNotFoundError:
    print("File does not exist or no file entered")
except:
    print("Some error with file")

# start of main chunk remove opcodes from rest of code; so left with everything else
for b, binaries in enumerate(listbinary): # creates array with key as index;
    for key in  ops.keys():
        if str(key) in binaries:
            #append instructions with the key
            instruction.append(ops[key])
            listbinary[b] = listbinary[b].replace(str(key), "") # gets rid of instr portion of binary
            break 

# instructions


for i, instr in enumerate(instruction):


    opcode = instr[0]
    
    # calls type functions to replace instruction[i] with full name
    
    instruction[i] = instr[1](opcode, listbinary[i], i)

    if i in labels.keys():
        print(labels[i] + ":")
    print(instr)


 
       
