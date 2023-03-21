from ase.io import read
from ase import atoms
import numpy as np
import os, sys
import glob
import shutil
from tqdm import tqdm
from scipy import stats
import matplotlib.pyplot as plt
np.set_printoptions(precision = 10)
#############################
# USER INPUT PARAMETER HERE #
#############################

# input data path here, string, this directory should contains
#   ./data/*frc-1.xyz ./data/*pos-1.xyz
#data_path = "./"
data_path = os.getcwd()
out_fileExt = r".out"
frc_filrExt = r"frc-1.xyz"
cell_fileExt = r".cell"
fileList=[_ for _ in os.listdir(data_path) if _.endswith(out_fileExt) or _.endswith(frc_filrExt) or _.endswith(cell_fileExt)]
wannier_list=[_ for _ in os.listdir(data_path) if 'HOMO_centers' in _]

#open data files
out_file=open(fileList[2])
frc_file=open(fileList[1])
cell_file=open(fileList[0])
if len(wannier_list)!=0:
    print('There is certain file of wannier center information')
    wannier_file=open(wannier_list[0])
else: print(('There is not certain file of wannier center information'))
#global au2A,au2eV


stress_tensor=[]
tag_num=-10
for i, line in enumerate(out_file):
    if '[a.u.] = [Bohr] -> [Angstrom]' in line:
        au2A=float(line.rstrip('\n').split()[-1])
    elif '[a.u.] -> [Pa]' in line:
        au2GPa=float(line.rstrip('\n').split()[-1])/10**9
    elif '[a.u.] -> [eV]' in line:
        au2eV=float(line.rstrip('\n').split()[-1])
    elif ' STRESS| Analytical stress tensor [GPa]' in line:
        tag_num=i
    elif tag_num+1<i<tag_num+5:
        stress_tensor.extend(line.rstrip('\n').split()[2:])
au2Deybe=1/0.393430307
stress_tensor=np.array(stress_tensor,dtype="float")
stress_tensor=np.reshape(stress_tensor,(len(stress_tensor)//9,9))

#the number of atom in system
atom_num = int(frc_file.readline().rstrip('\n').split()[-1])
water_num=int(data_path.split('\\')[-1].split('_')[1])
nacl_num=int(data_path.split('\\')[-1].split('_')[0])
####################
# START OF PROGRAM #
####################

def xyz2npy(pos, atom_num, output, unit_convertion=1.0):
    total = np.empty((0,atom_num*3), float)
    for single_pos in pos:
        tmp=single_pos.get_positions()
        tmp=np.reshape(tmp,(1,atom_num*3))
        total = np.concatenate((total,tmp), axis=0)
    total = total * unit_convertion
    np.savetxt(output, total)

def energy2npy(pos, output, unit_convertion=1.0):
     total = np.empty((0), float)
     for single_pos in pos:
         tmp=single_pos.info.pop('E')
         tmp=np.array(tmp,dtype="float")
         tmp=np.reshape(tmp,1)
         total = np.concatenate((total,tmp), axis=0)
     total = total * unit_convertion
     np.savetxt(output,total)

def cell2npy(pos, output, unit_convertion=1.0):
    total = np.empty((0,9),float)
    for single_pos in pos:
        tmp = np.array(single_pos.rstrip('\n').split()[2:-1], dtype="float")
        tmp = np.reshape(tmp, (1,9))
        total = np.concatenate((total,tmp),axis=0)
    total = total * unit_convertion
    np.savetxt(output,total)

def virial2npy(pos, output, unit_convertion=1.0):
    total = np.empty((0,9),float)
    for single_vol in pos:
        volume_instant=float(single_vol.rstrip('\n').split()[-1])
        tmp = volume_instant*stress_tensor[int(single_vol.rstrip('\n').split()[0])]
        tmp = np.reshape(tmp, (1,9))
        total = np.concatenate((total,tmp),axis=0)
    total = total * unit_convertion
    np.savetxt(output,total)

def dipole2npy(wa,water_num,nacl_num, output, unit_convertion=1.0):
    total = np.empty((0,(water_num+2*nacl_num)*3), float)
    o_index, ion_index, x_index , water_dipole_distri, nacl_dipole_distri= [[] for i in range(5)]

    for i, single_pos in enumerate(tqdm(wa)):
        tmp=[]
        cell_tmp = np.array(cell[i].rstrip('\n').split()[2:-1], dtype="float")
        cell_tmp = np.reshape(cell_tmp, (3,3))
        single_pos.set_cell(cell_tmp)
        single_pos.set_pbc((True, True, True))
        #posi_tmp = single_pos.get_positions(pbc=[1,1,1])
        if i==0:
            for j in range(len(single_pos)):
                if (single_pos.symbols=='O')[j]==True:
                    o_index.append(j)
                elif (single_pos.symbols=='Na')[j]==True:
                    ion_index.append(j)
                elif (single_pos.symbols=='Cl')[j]==True:
                    ion_index.append(j)
                elif (single_pos.symbols=='X')[j]==True:
                    x_index.append(j)
        #print(x_index)
        for k in o_index:
            contact_index=[]
            dis_OX_scale=single_pos.get_distances(k,x_index,mic=True)
            for l, line in enumerate(dis_OX_scale):
                if line < 1:
                    contact_index.append(x_index[l])
            dis_OX_vector=single_pos.get_distances(k, contact_index, mic=True, vector=True)
            #dis_OX_vector2=single_pos.get_distances(k, contact_index, mic=True)
            #print(dis_OX_vector1,-dis_OX_vector1.sum(axis=0),dis_OX_vector2)
            dis_OH_vector=single_pos.get_distances(k, [int(k*2+water_num),int(k*2+water_num+1)], mic=True, vector=True)
            sum=dis_OX_vector.sum(axis=0)
            H1_O=dis_OH_vector[0]
            H2_O = dis_OH_vector[1]
            #H2_H1=H2_O-H1_O
            # these three are equal
            dipole_O_center=6*(-sum)+-2*(-3*sum)-2*sum+1*H1_O+1*H2_O
            #dipole_X_center=1*(H1_O-sum)+1*(H2_O-sum)
            #dipole_H_center=-2*(sum-4*H1_O)+6*(-H1_O)+1*H2_H1
            #print(6*np.linalg.norm(x=sum),np.linalg.norm(x=dipole_O_center))
            #print(i, k, dipole_O_center*au2Deybe,dipole_X_center,dipole_H_center)
            tmp.append(dipole_O_center)
            water_dipole_distri.append(au2Deybe/au2A*np.linalg.norm(x=dipole_O_center))
        for k in ion_index:
            contact_index=[]
            dis_ionX_scale=single_pos.get_distances(k,x_index,mic=True)
            for l, line in enumerate(dis_ionX_scale):
                if line < 1:
                    contact_index.append(x_index[l])
            dis_ionX_vector=single_pos.get_distances(k, contact_index, mic=True, vector=True)
            #dis_OX_vector2=single_pos.get_distances(k, contact_index, mic=True)
            #print(dis_OX_vector1,-dis_OX_vector1.sum(axis=0),dis_OX_vector2)
            dipole_ion_center=-dis_ionX_vector.sum(axis=0)
            tmp.append(dipole_ion_center)
            #print(i,k,dipole_ion_center*au2Deybe)
            #print(i,k,-dis_ionX_vector.sum(axis=0),np.linalg.norm(x=dis_ionX_vector.sum(axis=0),ord=2))
            nacl_dipole_distri.append(au2Deybe/au2A*np.linalg.norm(x=dipole_ion_center))
        tmp = np.reshape(tmp, (1, (water_num+2*nacl_num)*3))
        total = np.concatenate((total, tmp), axis=0)
    total = total * unit_convertion
    np.savetxt(output, total)

    fig,(ax1,ax2)=plt.subplots(1, 2,sharey=False)
    plt.tight_layout()
    water_freq=stats.relfreq(water_dipole_distri,numbins=200)
    nacl_freq=stats.relfreq(nacl_dipole_distri,numbins=100)
    pdf_value_water=water_freq.frequency
    pdf_value_nacl = nacl_freq.frequency
    x_water=water_freq.lowerlimit+np.linspace(0,water_freq.binsize*water_freq.frequency.size,water_freq.frequency.size)
    x_nacl=nacl_freq.lowerlimit+np.linspace(0,nacl_freq.binsize*nacl_freq.frequency.size,nacl_freq.frequency.size)

    ax1.plot(x_water,pdf_value_water)
    ax1.axvline(1.855,color='darkred',label='EXP\n1.855',linestyle='--')
    ax1.axvline(2.2, color='green', label='SCAN\n2.2', linestyle='--')
    ax1.set_title('water dipole distribution')
    ax1.set_xlabel('dipole (Deybe)')
    ax1.legend(loc='best')

    ax2.plot(x_nacl, pdf_value_nacl)
    ax2.set_title('nacl dipole distribution')
    ax2.set_xlabel('dipole (Deybe)')

    plt.savefig(str(nacl_num)+'_'+str(water_num)+'_dipole_distribution.pdf',bbox_inches='tight')

def type_raw(single_pos, output):
    element = single_pos.get_chemical_symbols()
    element = np.array(element)
    tmp, indice = np.unique(element, return_inverse=True)
    np.savetxt(output, indice, fmt='%s',newline=' ')
np.savetxt("type_map.raw", ['O','H','Na','Cl'], fmt='%s',newline='\n')

# read the pos and frc
data_path = os.path.abspath(data_path)
pos_path = os.path.join(data_path, "*pos-1.xyz")
frc_path = os.path.join(data_path, "*frc-1.xyz")
wa_path = os.path.join(data_path, "*HOMO_centers*.xyz")
#print(data_path)
pos_path = glob.glob(pos_path)[0]
frc_path = glob.glob(frc_path)[0]
wa_path = glob.glob(wa_path)[0]
#print(pos_path)
#print(frc_path)
cell = cell_file.readlines()[1:]
pos = read(pos_path, index = ":" )
frc = read(frc_path, index = ":" )
wa = read(wa_path, index = ":" )

# numpy path
set_path = os.path.join(data_path, "set.000")
if os.path.isdir(set_path):
    print("detect directory exists\n now remove it")
    shutil.rmtree(set_path)
    os.mkdir(set_path)
else:
    print("detect directory doesn't exist\n now create it")
    os.mkdir(set_path)

type_path = os.path.join(data_path, "type.raw")
coord_path = os.path.join(set_path, "coord.raw")
force_path = os.path.join(set_path, "force.raw")
box_path = os.path.join(set_path, "box.raw")
virial_path = os.path.join(set_path, "virial.raw")
energy_path = os.path.join(set_path, "energy.raw")
dipole_path = os.path.join(set_path, "atomic_dipole.raw")

#tranforrmation
xyz2npy(pos, atom_num, coord_path)
xyz2npy(frc, atom_num, force_path, au2eV/au2A)
energy2npy(pos, energy_path, au2eV)
cell2npy(cell, box_path)
virial2npy(cell, virial_path, au2eV/(au2GPa*au2A**3))
type_raw(pos[0], type_path)
dipole2npy(wa, water_num,nacl_num, dipole_path, au2Deybe/au2A)
