#----------------------------------------------------------------------------
    # Created By: Lars Krupp, kruppl@rptu.de
    # Modified By: Nikolas Longen, nlongen@rptu.de
    # Reviewed By: Maximilian Kiefer-Emmanouilidis, maximilian.kiefer@rptu.de
    # Created: March 2023
    # Project: DCN QuanTUK
#----------------------------------------------------------------------------
from flask import render_template, request, session
# from qc_education_package import Simulator, DimensionalCircleNotation

from localtest import *
from flask import Flask

# Use non gui/interactive pyplot backend
import matplotlib
matplotlib.use('agg')

app = Flask(__name__)
app.config.from_object('config')


# ********************************* Open pages views ***************************************************


@app.route('/', methods=['GET', 'POST'])
# @log_access
def quantuk_generator():
    read_output = None
    if request.method == "GET":

        return render_template("quantuk_generator.html", # user=current_user,
                               visualized=None, q_bits=0, simulator=None, binary_label_list=[])

    else:
        posted_dict = request.form.to_dict()
        print(posted_dict)

        new_simulation = 'new_simulation' in posted_dict or 'simulator' in posted_dict and posted_dict['simulator'] == 'None'

        if new_simulation:
            try:
                q_bit_nr = int(posted_dict['q_bits'])
            except ValueError:
                try:
                    q_bit_nr = session['q_bits_nr_cookie']
                except KeyError:
                    q_bit_nr = 1

            sim = Simulator(q_bit_nr)
            session['q_bits_nr_cookie'] = q_bit_nr

        else:

            dont_look_at = ['csrf_token', 'simulator', 'q_bits', 'columns', 'control', 'notbit', 'cbit', 'angle',
                            'write', 'write_bit', 'write_complex', 'radio', 'read', 'control_bit', 'target_bit', 'cangle',
                            'rxangle', 'ryangle', 'rzangle', 'crxangle', 'cryangle', 'crzangle', 'show_values', 'visualization_method']
            sim_str = posted_dict['simulator']

            q_bit_nr = session['q_bits_nr_cookie']

            for i in range(0, 2**q_bit_nr):
                dont_look_at.append("betrag"+str(i))
                dont_look_at.append("phase" + str(i))

            try:
                control = posted_dict['control']
            except KeyError:
                control = ""
            print(sim_str)
            sim = Simulator(sim_str)


            if control == 'write':
                try:
                    write_bit = int(posted_dict['write_bit'])
                    if write_bit >= 2 ** q_bit_nr:
                        pass
                    else:
                        sim.write(write_bit)
                except ValueError:
                    pass


            elif control == 'write_complex':
                betrag_keys = []
                phase_keys = []
                for i in range(0, (2 ** q_bit_nr)):
                    betrag_keys.append("betrag" + str(i))
                    phase_keys.append("phase" + str(i))

                betrag_list = [0.0]*(2 ** q_bit_nr)
                for key in betrag_keys:
                    key_pos = int(key.replace("betrag", ""))

                    try:
                        betrag_list[key_pos] = float(posted_dict[key])
                    except ValueError:
                        pass

                phase_list = [0.0] * (2 ** q_bit_nr)
                for key in phase_keys:
                    key_pos = int(key.replace("phase", ""))
                    try:
                        phase_list[key_pos] = float(posted_dict[key])
                    except ValueError:
                        pass

                if betrag_list != [0.0]*(2 ** q_bit_nr):# and phase_list != [0.0]*(2 ** q_bit_nr):
                    sim.writeMagnPhase(betrag_list, phase_list)


            elif control == 'read':
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))

                if control_bits == 0:
                    control_bits = None

                read_output, result = sim.read(control_bits)

            
            elif control == "check_seperability":
                pass


            elif control == 'Set global Phase to 0':
                sim.setGlobalPhase0()


            elif control == "qnot" or control == "x":
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0:
                    sim.qnot(control_bits)
            
            elif control == "y":
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0:
                    sim.y(control_bits)

            elif control == "z":
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0:
                    sim.z(control_bits)

            elif control == "rootX":
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0:
                    sim.rootX(control_bits)
            
            elif control == "rootZ":
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0:
                    sim.rootZ(control_bits)



            elif control == "had":
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0:
                    sim.had(control_bits)
            

            elif control == 'swap':
                control_bits = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                # print("swap", q_bits_2_apply)
                if len(control_bits) == 2:
                    sim.swap(control_bits[0], control_bits[1])


            elif control == "phase":
                try:
                    angle = int(posted_dict['angle'])
                    control_bits = []
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            control_bits.append(int(key))
                    sim.phase(angle=angle, qubit=control_bits)
                except (ValueError, KeyError):
                    pass
       
            
            elif control == 'rx':
                try:
                    angle = int(posted_dict['rxangle'])
                    c_bit = int(posted_dict['control_bit'])
                    if c_bit == 0:
                        sim.rx(angle, None)
                    else:
                        sim.rx(angle, c_bit)
                except (ValueError, KeyError):
                    pass


            elif control == 'ry':
                try:
                    angle = int(posted_dict['ryangle'])
                    c_bit = int(posted_dict['control_bit'])
                    if c_bit == 0:
                        sim.ry(angle, None)
                    else:
                        sim.ry(angle, c_bit)
                except (ValueError, KeyError):
                    pass


            elif control == 'rz':
                try:
                    angle = int(posted_dict['rzangle'])
                    c_bit = int(posted_dict['control_bit'])
                    if c_bit == 0:
                        sim.rz(angle, None)
                    else:
                        sim.rz(angle, c_bit)
                except (ValueError, KeyError):
                    pass


            elif control == "cnot":
                try:
                    target_bit = int(posted_dict['target_bit'])
                    control_bit = int(posted_dict['control_bit'])

                    if target_bit != control_bit:
                        sim.cNot(control_bit, target_bit)
                except (KeyError, ValueError):
                    pass


            elif control == "chad":
                control_bits = []
                try:
                    control_bit = int(posted_dict['control_bit'])
                except KeyError:
                    control_bit = -1
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        control_bits.append(int(key))
                if len(control_bits) > 0 and control_bit != -1:
                    sim.cHad(control_bit, control_bits)

            
            elif control == "cswap":
                try:
                    control_bit = int(posted_dict['control_bit'])
                    control_bits = []
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            control_bits.append(int(key))
                    # print("swap", q_bits_2_apply)
                    if len(control_bits) == 2 and control_bit not in control_bits:
                        sim.cSwap([control_bit], control_bits[0], control_bits[1])
                except KeyError:
                    pass



            elif control == 'cphase':
                try:
                    target_bit = int(posted_dict['target_bit'])
                    control_bit = int(posted_dict['control_bit'])
                    angle = int(posted_dict['cangle'])
                    sim.cPhase(angle, control_bit, target_bit)
                except KeyError:
                    pass


            elif control == 'crx':
                try:
                    angle = int(posted_dict['crxangle'])
                    c_bit = int(posted_dict['control_bit'])
                    n_bit = int(posted_dict['target_bit'])
                    sim.cRx(angle, c_bit, n_bit)
                except (ValueError, KeyError):
                    pass


            elif control == 'cry':
                try:
                    angle = int(posted_dict['cryangle'])
                    c_bit = int(posted_dict['control_bit'])
                    n_bit = int(posted_dict['target_bit'])
                    sim.cRy(angle, c_bit, n_bit)
                except (ValueError, KeyError):
                    pass


            elif control == 'crz':
                try:
                    angle = int(posted_dict['crzangle'])
                    c_bit = int(posted_dict['control_bit'])
                    n_bit = int(posted_dict['target_bit'])
                    sim.cRz(angle, c_bit, n_bit)
                except (ValueError, KeyError):
                    pass


            elif control == 'ccnot':
                try:
                    target_bit = int(posted_dict['target_bit'])
                    # control_bit = int(posted_dict['control_bit'])
                    control_bits = []
                    # for i in range(q_bit_nr):
                    #     control_bits.append()
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            control_bits.append(int(key))
                    if target_bit in control_bits:
                        control_bits.remove(target_bit)
                    sim.cNot(control_bits, target_bit)
                except (ValueError, KeyError):
                    pass
            
        # Select Visualizer values?
        try:
            visName = posted_dict["visualization_method"]
        except KeyError:
            visName = 'DCN'

        if visName == 'DCN':
            vis = DimensionalCircleNotation(sim)
        elif visName == 'CN':
            vis = CircleNotation(sim)
        else:
            raise Exception(f'Wrong value: No such visualizer in views.py: {posted_dict}')

        # Show values?
        try:
            show_values = bool(int(posted_dict["show_values"]))
        except KeyError:
            show_values = False
        vis.showMagnPhase(show_values)
        
        
        # construct binary label list
        binary_label_list = []
        max_len = len(format(2**q_bit_nr-1, 'b'))
        for i in range(0, 2**q_bit_nr):
            binary = format(i, 'b')
            diff = max_len-len(binary)
            if diff > 0:
                binary = "0"*diff+binary
            binary_label_list.append(binary)

        return render_template("quantuk_generator.html", # user=current_user,
                               visualized=vis.exportBase64("png"),
                               visualized_pdf=vis.exportBase64("pdf"),
                               visualized_svg=vis.exportBase64("svg"),
                               q_bits=q_bit_nr, simulator=sim.toJson(), read_output=read_output, show_values=show_values, visualization_method=visName,
                               binary_label_list=binary_label_list)

                               