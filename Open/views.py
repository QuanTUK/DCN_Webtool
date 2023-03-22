from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from ..models import User, Rat, Comment, Help_material
from .. import db
from flask import Markup
from ..blueprints import views
from ..log_user_interactions import log_access
from ..configuration import get_config
from .simulator import simulator
from .visualization import CircleNotation, DimensionalCircleNotation
import numpy as np
import os
import ast

configuration = get_config()


# ********************************* Open pages views ***************************************************
@views.route('/', methods=['GET', 'POST'])
@log_access
# @login_required
def home():
    # return "<h1>KI4TUK</h1>"
    #return render_template("home.html", user=current_user)

    if current_user.is_authenticated:           #User is logged in
        if current_user.user_rights == 1:               #User is student
            return redirect(url_for('views.profile'))
        elif current_user.user_rights == 2:             #User creates Rats
            if not current_user.rats:
               return redirect(url_for('views.rats_category', status='All'))
            else:
               return redirect(url_for('views.my_rats'))
        elif current_user.user_rights == 3:             #User is lecturer
            return redirect(url_for('views.my_lectures'))
        elif current_user.user_rights == 4:             #User is admin
            return redirect(url_for('views.admin'))
        else:
            return render_template("home.html", user=current_user)
    else:                                         #User is not logged in
        return render_template("home.html", user=current_user)


@views.route('/mission')
@views.route('mission')
@log_access
def mission():
    return render_template("Open/mission.html", user=current_user)


@views.route('/project')
@views.route('project')
@log_access
def project():
    return render_template("Open/project.html", user=current_user)


@views.route('/contact')
@views.route('contact')
@log_access
def contact():
    return render_template("Open/contact.html", user=current_user)


@views.route('/impressum')
@views.route('impressum')
@log_access
def impressum():
    return render_template("Open/impressum.html", user=current_user)


@views.route('/verlosung')
@views.route('verlosung')
@log_access
def lottery():
    return render_template("Open/lottery_information.html", user=current_user)


@views.route('/information_window/<info>', methods=['GET'])
@views.route('information_window/<info>', methods=['GET'])
@log_access
@login_required
def embedded_information_window(info):
    return render_template("Information/"+info+".html", user=current_user)

@log_access
@login_required
def welcome():
    return render_template("Login/welcome_page.html", user=current_user)

@views.route('/privacy_policy')
@views.route('privacy_policy')
@log_access
def privacy_policy():
    return render_template("Open/privacy_policy.html", user=current_user)


@views.route('/how_to_rats_app')
@views.route('how_to_rats_app')
@log_access
def how_to_rats_app():
    video_path="/static/videos/How_to_RatsApp.mp4"
    return render_template("Open/video_page.html", user=current_user, video_path=video_path,
                           video_title="Wie funktioniert RatsApp?")


# @views.route('/motivation')
# @views.route('motivation')
@log_access
def rats_app_motivation():
    video_path="/static/videos/RatsApp - Be a part.mp4"
    return render_template("Open/video_page.html", user=current_user, video_path=video_path,
                           video_title="Wieso RatsApp?")


@views.route('/quantuk', methods=['GET', 'POST'])
@views.route('quantuk', methods=['GET', 'POST'])
@log_access
def quantuk_generator():
    read_output = None
    if request.method == "GET":

        return render_template("Open/quantuk_generator.html", user=current_user, visualized=None, q_bits=0, simulator=None, binary_label_list=[])

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
                    q_bit_nr = 2
            sim = simulator(q_bit_nr)
            session['q_bits_nr_cookie'] = q_bit_nr

        else:
            # print("keep old simulation")
            # print(posted_dict.keys())
            dont_look_at = ['csrf_token', 'simulator', 'q_bits', 'columns', 'control', 'notbit', 'cbit', 'angle',
                            'write', 'write_bit', 'write_complex', 'radio', 'read', 'c_bit', 'n_bit', 'cangle',
                            'rxangle', 'ryangle', 'rzangle', 'crxangle', 'cryangle', 'crzangle']
            sim_str = posted_dict['simulator']
            # colum_nr = session['columns_cookie']
            q_bit_nr = session['q_bits_nr_cookie']

            for i in range(0, 2**q_bit_nr):
                dont_look_at.append("betrag"+str(i))
                dont_look_at.append("phase" + str(i))
            # print(dont_look_at)
            control = posted_dict['control']
            sim = simulator(jsonDump=sim_str)

            if control == "phase":
                try:
                    angle = int(posted_dict['angle'])
                    q_bits_2_apply = []
                    for key in posted_dict.keys():
                        if key not in dont_look_at:
                            q_bits_2_apply.append(int(key))
                    sim.phase(angle=angle, Q_bit=q_bits_2_apply)
                except ValueError:
                    pass

            elif control == "qnot":
                q_bits_2_apply = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                sim.qnot(q_bits_2_apply)

            elif control == "had":
                q_bits_2_apply = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                sim.had(q_bits_2_apply)

            elif control == "cnot":
                try:
                    not_bit = int(posted_dict['n_bit'])
                    control_bit = int(posted_dict['c_bit'])

                    if not_bit != control_bit:
                        sim.cNot(control_bit, not_bit)
                except ValueError:
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
                    sim.write_abs_phase(betrag_list, phase_list)

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
                except ValueError:
                    pass

            elif control == 'ry':
                try:
                    angle = int(posted_dict['ryangle'])
                    c_bit = int(posted_dict['c_bit'])
                    if c_bit == 0:
                        sim.ry(angle, None)
                    else:
                        sim.ry(angle, c_bit)
                except ValueError:
                    pass

            elif control == 'rz':
                try:
                    angle = int(posted_dict['rzangle'])
                    c_bit = int(posted_dict['c_bit'])
                    if c_bit == 0:
                        sim.rz(angle, None)
                    else:
                        sim.rz(angle, c_bit)
                except ValueError:
                    pass

            elif control == 'crx':
                try:
                    angle = int(posted_dict['crxangle'])
                    c_bit = int(posted_dict['c_bit'])
                    n_bit = int(posted_dict['n_bit'])
                    sim.cRx(c_bit, n_bit, angle)
                except ValueError:
                    pass

            elif control == 'cry':
                try:
                    angle = int(posted_dict['cryangle'])
                    c_bit = int(posted_dict['c_bit'])
                    n_bit = int(posted_dict['n_bit'])
                    sim.cRx(c_bit, n_bit, angle)
                except ValueError:
                    pass

            elif control == 'crz':
                try:
                    angle = int(posted_dict['crzangle'])
                    c_bit = int(posted_dict['c_bit'])
                    n_bit = int(posted_dict['n_bit'])
                    sim.cRx(c_bit, n_bit, angle)
                except ValueError:
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
                except ValueError:
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
                control_bit = int(posted_dict['c_bit'])
                q_bits_2_apply = []
                for key in posted_dict.keys():
                    if key not in dont_look_at:
                        q_bits_2_apply.append(int(key))
                # print("swap", q_bits_2_apply)
                if len(q_bits_2_apply) == 2 and control_bit not in q_bits_2_apply:
                    sim.cSwap([control_bit], q_bits_2_apply[0], q_bits_2_apply[1])

        vis = DimensionalCircleNotation(sim)
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

        return render_template("Open/quantuk_generator.html", user=current_user, visualized=vis.export_base64("png"),
                               visualized_pdf=vis.export_base64("pdf"),
                               q_bits=q_bit_nr, simulator=str(sim), read_output=read_output,
                               binary_label_list=binary_label_list)


