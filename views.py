#----------------------------------------------------------------------------
    # Created By: Lars Krupp, kruppl@rptu.de
    # Modified By: Nikolas Longen, nlongen@rptu.de
    # Reviewed By: Maximilian Kiefer-Emmanouilidis, maximilian.kiefer@rptu.de
    # Created: March 2023
    # Project: DCN QuanTUK
#----------------------------------------------------------------------------
from flask import Flask, render_template, request, session
from qc_education_package import Simulator


# Use non gui/interactive pyplot backend
import matplotlib
matplotlib.use('agg')

app = Flask(__name__)
app.config.from_object('config')

# ********************************* Open pages views ***************************************************
@app.route('/', methods=['GET', 'POST'])
def quantuk_generator():
    read_output = None
    if request.method == "GET":
        return render_template("quantuk_generator.html", visualized=None, q_bits=0, simulator=None, binary_label_list=[])
    else:
        posted_dict = request.form.to_dict()
        print(f"\nPosted dict: {posted_dict}\n")
        # TODO: Store meta informatoins in session cookie
        # Select Visualizer values?
        try:
            visName = posted_dict["visualization_method"]
        except KeyError:
            visName = 'DCN'
        try:
            visVersion = posted_dict["vis_version"]
        except KeyError:
            visVersion = '2'

        # Only import chosen visualizer
        if visName == 'DCN':
            from qc_education_package import DimensionalCircleNotation as Visualizer
        elif visName == 'CN':
            from qc_education_package import CircleNotation as Visualizer
        else:
            raise Exception(f'Wrong value: No such visualizer in views.py: {posted_dict}')

        new_simulation = 'new_simulation' in posted_dict or 'simulator' in posted_dict and posted_dict['simulator'] == 'None'
        if new_simulation:
            # new state has to be created
            try:
                q_bit_nr = int(posted_dict['q_bits'])
            except ValueError:
                try:
                    q_bit_nr = session['q_bits_nr_cookie']
                except KeyError:
                    q_bit_nr = 1

            session['q_bits_nr_cookie'] = q_bit_nr
            sim = Simulator(q_bit_nr, 'version', visVersion) # Version as optional argument
        else:
            # Gate was applied to existing state
            sim_str = posted_dict['simulator']
            q_bit_nr = session['q_bits_nr_cookie']

            # get info about the gate to be applied
            # Gate 
            try:
                control = posted_dict['control']
            except KeyError:
                control = ""
            print(f"Sim String: \n {sim_str:s}\n")
            sim = Simulator(sim_str)
            # Involved qubits 
            target_bits = []
            control_bits = []
            for key, val in posted_dict.items():
                    if key.startswith('target_bit'):
                        target_bits.append(int(val))
                    if key.startswith('control_bit'):
                        control_bits.append(int(val))
            # Angle parameter for phase gates
            # Only search the suitable angle for the gate
            # Currently all forms in modals are submitted each time, hence the angles of the phase gates need a unique key/name...
            angle_key = f'{control}_angle'
            if angle_key in posted_dict.keys() and posted_dict[angle_key] != '':
                angle = int(posted_dict[angle_key])
            else :
                angle = 0
            
            print(f"\nControl is {control}\nTarget bits are {*target_bits,}\nControl bits are {*control_bits,}\nAngle is {angle}\n")
            
            if len(target_bits) == 0:
                target_bits = None # Apply to all qubits if None are selected
                # TODO: Give info in gate description that all qubits are affected when none selected
            
            # Apply chosen gate
            if control == 'write':
                try:
                    write_bit = int(posted_dict['write_bit'])
                    if write_bit < 2 ** q_bit_nr:
                        sim.write(write_bit)
                    else:
                        print("Error: Write bit is out of range.")
                except ValueError:
                    print("Value Error in control==write")

            elif control == 'write_complex':
                # Keys are sorted in ascending order, so appending will guarantee the correct order
                val_list = []
                phase_list = []
                for i in range(0, (2 ** q_bit_nr)):
                    try:
                        val_list.append(float(posted_dict[f"val_{i}"]))
                        phase_list.append(float(posted_dict[f"phase_{i}"]))
                    except ValueError:
                        print("Value Error in control==write_complex")
                print(f"Val List: {val_list}\nPhase List: {phase_list}")
                if val_list != [0.0]*(2 ** q_bit_nr):
                    sim.writeMagnPhase(val_list, phase_list)

            elif control == 'read':
                read_output, _ = sim.read(target_bits)

            elif control == "check_seperability":
                pass # TODO

            elif control == 'Set global Phase to 0':
                sim.setGlobalPhase0()

            elif control == "qnot" or control == "x":
                    sim.qnot(target_bits)
            
            elif control == "y":
                    sim.y(target_bits)

            elif control == "z":
                    sim.z(target_bits)

            elif control == "rootX":
                    sim.rootX(target_bits)
            
            elif control == "rootZ":
                    sim.rootZ(target_bits)

            elif control == "had":
                    sim.had(target_bits)
            
            elif control == 'swap':
                if len(target_bits) == 2:
                    sim.swap(target_bits[0], target_bits[1])

            elif control == "phase":
                sim.phase(angle, target_bits)
            
            elif control == 'rx':
                sim.rx(angle, target_bits)

            elif control == 'ry':
                sim.ry(angle, target_bits)

            elif control == 'rz':
                sim.rz(angle, target_bits)

            # Controlled Gates are only applied to one target bit. We assume that web fronted does this somehow correctly.
            # So list only contains one element.
            elif control == "cnot":
                sim.cNot(control_bits, target_bits[0])

            elif control == "chad":
                if len(control_bits) > 0 and target_bits[0] != -1:
                    sim.cHad(control_bits, target_bits)

            elif control == "cswap":
                if len(target_bits) == 2 and target_bits[0] not in control_bits and target_bits[1] not in control_bits:
                    sim.cSwap(control_bits, target_bits[0], target_bits[1])
                else:
                    raise Exception("Error: cSwap: Target bits are not unique or one of them is a control bit.")

            elif control == 'cphase':
                sim.cPhase(angle, control_bits, target_bits[0])

            elif control == 'crx':
                sim.cRx(angle, control_bits, target_bits[0])

            elif control == 'cry':
                sim.cRy(angle, control_bits, target_bits[0])

            elif control == 'crz':
                sim.cRz(angle, control_bits, target_bits[0])

            elif control == 'ccnot':
                sim.cNot(control_bits, target_bits[0])
                
            else: # base case
                print('Error: Unknown gate name...')
            
        # Create visualizer
        vis = Visualizer(sim)
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

        
        FormattedGateNames = {"x": "Not", "y":"Y", "z":"Z", "rootx":"Root-X", "rootz":"Root-Z", "cnot":"cNot", "cy":"cY", "cz":"cZ", "had":"Had", "chad":"cHad", 
                              "phase":"Phase", "cphase":"cPhase", "rx":"Rx", "ry":"Ry", "rz":"Rz", "crx":"cRx", "cry":"cRy", "crz":"cRz", "read":"Read", }
        
        return render_template("quantuk_generator.html", # user=current_user,
                               visualized=vis.exportBase64("png"),
                               visualized_pdf=vis.exportBase64("pdf"),
                               visualized_svg=vis.exportBase64("svg"),
                               q_bits=q_bit_nr, simulator=sim.toJson(), read_output=read_output, show_values=show_values, visualization_method=visName,
                               vis_version=visVersion, binary_label_list=binary_label_list, FormattedGateNames=FormattedGateNames)

