#----------------------------------------------------------------------------
    # Created By: Lars Krupp, kruppl@rptu.de
    # Modified By: Nikolas Longen, nlongen@rptu.de
    # Reviewed By: Maximilian Kiefer-Emmanouilidis, maximilian.kiefer@rptu.de
    # Created: March 2023
    # Project: DCN QuanTUK
#----------------------------------------------------------------------------
from flask import render_template, request, session
from qc_education_package import Simulator, DimensionalCircleNotation
from flask import Flask

import matplotlib
matplotlib.use('agg')

app = Flask(__name__)
app.config['SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'

# configuration = get_config()


# ********************************* Open pages views ***************************************************


@app.route('/', methods=['GET', 'POST'])
# @log_access
def quantuk_generator():
    read_output = None
    if request.method == "GET":

        return render_template("quantuk_generator.html", # user=current_user,
                               visualized=None, q_bits=0, simulator=None, binary_label_list=[])

    else:
        # sim = simulator()
        posted_dict = request.form.to_dict()
        print(posted_dict)

        try:
            new_simulation = posted_dict['new_simulation']
        except KeyError:
            new_simulation = False
        #
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
            # print("keep old simulation")
            # print(posted_dict.keys())
            dont_look_at = ['csrf_token', 'simulator', 'q_bits', 'columns', 'control', 'notbit', 'cbit', 'angle',
                            'write', 'write_bit', 'write_complex', 'radio', 'read', 'c_bit', 'n_bit', 'cangle',
                            'rxangle', 'ryangle', 'rzangle', 'crxangle', 'cryangle', 'crzangle', 'show_values']
            sim_str = posted_dict['simulator']
            # colum_nr = session['columns_cookie']
            q_bit_nr = session['q_bits_nr_cookie']

            for i in range(0, 2**q_bit_nr):
                dont_look_at.append("betrag"+str(i))
                dont_look_at.append("phase" + str(i))
            # print(dont_look_at)
            control = posted_dict['control']
            sim = Simulator(jsonDump=sim_str)

            if control == "phase":
                try:
                    angle = int(posted_dict['angle'])
                    q_bits_2_apply = []
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            q_bits_2_apply.append(int(key))
                    sim.phase(angle=angle, Q_bit=q_bits_2_apply)
                except (ValueError, KeyError):
                    pass

            elif control == "qnot":
                q_bits_2_apply = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                if len(q_bits_2_apply) > 0:
                    sim.qnot(q_bits_2_apply)

            elif control == "had":
                q_bits_2_apply = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                if len(q_bits_2_apply) > 0:
                    sim.had(q_bits_2_apply)

            elif control == "chad":
                q_bits_2_apply = []
                try:
                    control_bit = int(posted_dict['c_bit'])
                except KeyError:
                    control_bit = -1
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                if len(q_bits_2_apply) > 0 and control_bit != -1:
                    sim.cHad(q_bits_2_apply, control_bit)

            elif control == "cnot":
                try:
                    not_bit = int(posted_dict['n_bit'])
                    control_bit = int(posted_dict['c_bit'])

                    if not_bit != control_bit:
                        sim.cNot(control_bit, not_bit)
                except (KeyError, ValueError):
                    pass

            elif control == 'write':
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

                phase_list = [0] * (2 ** q_bit_nr)
                for key in phase_keys:
                    key_pos = int(key.replace("phase", ""))
                    try:
                        phase_list[key_pos] = int(posted_dict[key])
                    except ValueError:
                        pass

                if betrag_list != [0.0]*(2 ** q_bit_nr) and phase_list != [0.0]*(2 ** q_bit_nr):
                    sim.write_magn_phase(betrag_list, phase_list)

                """
                for betrag, phase in zip(betrag_list, phase_list):
                    value = betrag * np.exp(1j * np.deg2rad(phase))

                    # value = betrag * np.exp(1j*phase)
                    complex_results.append(value)
                sim.write_complex(complex_results)
                """
            elif control == 'read':
                q_bits_2_apply = 0
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply = int(key)

                if q_bits_2_apply == 0:
                    q_bits_2_apply = None

                read_output = sim.read(q_bits_2_apply)

            elif control == 'rx':
                try:
                    angle = int(posted_dict['rxangle'])
                    c_bit = int(posted_dict['c_bit'])
                    if c_bit == 0:
                        sim.rx(angle, None)
                    else:
                        sim.rx(angle, c_bit)
                except (ValueError, KeyError):
                    pass

            elif control == 'ry':
                try:
                    angle = int(posted_dict['ryangle'])
                    c_bit = int(posted_dict['c_bit'])
                    if c_bit == 0:
                        sim.ry(angle, None)
                    else:
                        sim.ry(angle, c_bit)
                except (ValueError, KeyError):
                    pass

            elif control == 'rz':
                try:
                    angle = int(posted_dict['rzangle'])
                    c_bit = int(posted_dict['c_bit'])
                    if c_bit == 0:
                        sim.rz(angle, None)
                    else:
                        sim.rz(angle, c_bit)
                except (ValueError, KeyError):
                    pass

            elif control == 'crx':
                try:
                    angle = int(posted_dict['crxangle'])
                    c_bit = int(posted_dict['c_bit'])
                    n_bit = int(posted_dict['n_bit'])
                    sim.cRx(c_bit, n_bit, angle)
                except (ValueError, KeyError):
                    pass

            elif control == 'cry':
                try:
                    angle = int(posted_dict['cryangle'])
                    c_bit = int(posted_dict['c_bit'])
                    n_bit = int(posted_dict['n_bit'])
                    sim.cRx(c_bit, n_bit, angle)
                except (ValueError, KeyError):
                    pass

            elif control == 'crz':
                try:
                    angle = int(posted_dict['crzangle'])
                    c_bit = int(posted_dict['c_bit'])
                    n_bit = int(posted_dict['n_bit'])
                    sim.cRx(c_bit, n_bit, angle)
                except (ValueError, KeyError):
                    pass

            elif control == 'swap':
                q_bits_2_apply = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                # print("swap", q_bits_2_apply)
                if len(q_bits_2_apply) == 2:
                    sim.swap(q_bits_2_apply[0], q_bits_2_apply[1])

            elif control == 'ccnot':
                try:
                    not_bit = int(posted_dict['n_bit'])
                    # control_bit = int(posted_dict['c_bit'])
                    q_bits_2_apply = []
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            q_bits_2_apply.append(int(key))
                    if not_bit in q_bits_2_apply:
                        q_bits_2_apply.remove(not_bit)
                    sim.cNot(q_bits_2_apply, not_bit)
                except (ValueError, KeyError):
                    pass
            elif control == 'cphase':
                try:
                    not_bit = int(posted_dict['n_bit'])
                    control_bit = int(posted_dict['c_bit'])
                    angle = int(posted_dict['cangle'])
                    sim.cPhase(control_bit, not_bit, angle)
                except KeyError:
                    pass

            elif control == 'Set global Phase to 0':
                sim.setGlobalPhase0()
            elif control == "cswap":
                try:
                    control_bit = int(posted_dict['c_bit'])
                    q_bits_2_apply = []
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            q_bits_2_apply.append(int(key))
                    # print("swap", q_bits_2_apply)
                    if len(q_bits_2_apply) == 2 and control_bit not in q_bits_2_apply:
                        sim.cSwap([control_bit], q_bits_2_apply[0], q_bits_2_apply[1])
                except KeyError:
                    pass

            elif control == "check_seperability":
                pass

        print("posted", posted_dict)
        try:
            print("sv", posted_dict["show_values"])
            if posted_dict["show_values"] == "1":
                show_values = True
            else:
                show_values = False
        except KeyError:
            show_values = False
        vis = DimensionalCircleNotation(sim, show_values)
        vis.draw()
        binary_label_list = []

        # construct binary label list
        max_len = len(format(2**q_bit_nr-1, 'b'))
        for i in range(0, 2**q_bit_nr):
            binary = format(i, 'b')
            diff = max_len-len(binary)
            if diff > 0:
                binary = "0"*diff+binary
            binary_label_list.append(binary)

        # print(binary_label_list)

        return render_template("quantuk_generator.html", # user=current_user,
                               visualized=vis.export_base64("png"),
                               visualized_pdf=vis.export_base64("pdf"),
                               q_bits=q_bit_nr, simulator=str(sim), read_output=read_output,
                               binary_label_list=binary_label_list)


app.run(debug=True)


