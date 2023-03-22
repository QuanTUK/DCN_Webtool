import numpy as np
from numpy.random import rand
import json


class simulator():

    def __init__(self, n=None, jsonDump=None):
        """Constructor for quantum simulator. Creates simulator for n Q-bits.
        Q-bits are indexed from 1 to n, registers from 1 to N=2**n

        Args:
            n (int): Number of Q-bits, optional
            jsonDump (str): JSON Dump to restore simulator state from, optional
        """
        # Prepare Q-bit base states
        self._zero = np.array([[1], [0]])
        self._one = np.array([[0], [1]])
        # Prepare one Q-bit gates/matrices
        self._I = np.identity(2)  # Identity in C2
        self._H = 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]])  # Hadamard gate
        self._X = np.array([[0, 1], [1, 0]])  # Not or Pauli X gate
        self._Y = np.array([[0, -1j], [1j, 0]])  # Pauli Y gate
        self._Z = np.array([[1, 0], [0, -1]])  # Phase 180 or Pauli Z gate
        self._ROOTX = np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) / 2  # Phase 180 or Z gate
        self._ROOTZ = np.array([[1, 0], [0, 1j]])  # Phase 180 or Z gate

        self._P = lambda phi: np.array([[1, 0], [0, np.exp(1j * phi)]], dtype=complex)  # General phase gate
        self._Rx = lambda phi: np.array(
            [[np.cos(phi / 2), -1j * np.sin(phi / 2)], [-1j * np.sin(phi / 2), np.cos(phi / 2)]],
            dtype=complex)  # Rotation about x-axis (Bloch Sphere)
        self._Ry = lambda phi: np.array([[np.cos(phi / 2), -1 * np.sin(phi / 2)], [np.sin(phi / 2), np.cos(phi / 2), ]],
                                        dtype=complex)  # Rotation about y-axis (Bloch Sphere)
        self._Rz = lambda phi: np.array([[np.exp(-1j * phi / 2), 0], [0, np.exp(-1j * phi / 2)]],
                                        dtype=complex)  # Rotation about z-axis (Bloch Sphere)

        if jsonDump is not None:
            state = json.loads(jsonDump)
            self._n = int(state['n'])
            amp = np.array(state['amp'])
            phase = np.array(state['phase'])
            self._register = amp * np.exp(1j * phase)
            self._Q_bits = [self._zero] * self._n  # for showing start state in quantum circuit
        else:
            assert (n > 0)
            self._n = n
            # Q-bit register
            self._Q_bits = [self._zero] * self._n  # for showing start state in quantum circuit
            self._register = self._nKron(self._Q_bits)
        self._basis = np.identity(2 ** self._n)

    def __str__(self):
        """Override toString to export simulator in json format

        Returns:
            str: n and register amplitudes and phases in json format
        """
        amp = np.abs(self._register).flatten().tolist()
        phase = np.angle(self._register).flatten().tolist()
        return json.dumps({'n': self._n, 'amp': amp, 'phase': phase})

    def reset(self, n=None):
        """Reset simulator to a system of n Q-bits with all Q-bits in state |0> (zero state).
        If n is not specified, resets all current Q-bits to |0>.

        Args:
            n (int, optional): Number of Q-bits in simulator.
        """
        if n is not None:
            self._n = n
            self._basis = np.identity(2 ** n)
        self._Q_bits = [self._zero] * self._n  # for showing start state in quantum circuit
        self._register = self._nKron(self._Q_bits)

    def write_integer(self, val: int, Q_bit=1):
        """Write given integer value in binary starting a position Q-bit. If no Q-bit parameter is passed, start
        with first Q-bit. Attention! This will override the register. Use this only to prepare your Q-bits/register.

        Args:
            val (integer): State is build to (1-p)|0> + p|1>. Hence p=0 -> |0>; p=1 -> |1>
            Q_bit (int, optional): Q-bit to be set. Defaults to 1.
        """
        # Check if val can be represented by n_Q_bit Q-bits
        assert (val < 2 ** (self._n - Q_bit + 1))
        i = Q_bit
        for d in format(val, 'b')[::-1]:
            self._Q_bits[-i] = self._one if d == '1' else self._zero
            i += 1
        self._register = self._nKron(self._Q_bits)

        # Alias to be compatible with qc engine

    # TODO overload write for int and list?
    def write(self, val: int, Q_bit=1):
        """Write given integer value in binary starting a position Q-bit. If no Q-bit parameter is passed, start
        with first Q-bit. Attention! This will override the register. Use this only to prepare your Q-bits/register.
        Alias for qc_simulator.write_integer(val, Q-Bit)

        Args:
            p (float or list): State is build to (1-p)|0> + p|1>. Hence p=0 -> |0>; p=1 -> |1>
            Q_bit (int or list, optional): Q-bit(s) to be set. Defaults to None.
        """
        self.write_integer(val, Q_bit)

    def write_prop(self, p: float, Q_bit=None):
        """Prepare Q-bit i into given state ((1-p)|0> + p|1>). If no Q-bit is given (Q_bit=None) prepare all Q-bits
        to given state. Attention! This will override the register. Use this only to prepare your Q-bits/register.
        p=0 -> Q_bit=|0>
        p=1 -> Q_bit=|1>

        Args:
            p (float or list): State is build to (1-p)|0> + p|1>. Hence p=0 -> |0>; p=1 -> |1>
            Q_bit (int or list, optional): Q-bit(s) to be set. Defaults to None.
        """
        if p is float:
            if Q_bit is None:
                self._register = self._nKron([(1 - p) * self._zero + p * self._one] * self._n)  # this is normed
            else:
                self._Q_bits[-Q_bit] = (1 - p) * self._zero + p * self._one  # -Q-bit s.t. order of registers is correct
        elif p is list:
            assert (Q_bit is list and len(Q_bit) == len(p))
            for pi in p:
                self._Q_bits[-Q_bit] = (1 - p) * self._zero + p * self._one  # -Q-bit s.t. order of registers is correct
        else:
            raise Exception(
                "Wrong parameter type in write_prop. Expecting float, (int) or list [of float], list [of int]")
        self._register = self._nKron(self._Q_bits)

    def write_complex(self, a):
        """Prepare register with given complex amplitudes e.g. reg = a0 |0> + a1 |1>
        Attention! This will override the register. Use this only to prepare your Q-bits/register.

        Args:
            a (list of float): Complex amplitude for each component
        """
        assert (len(a) == 2 ** self._n)
        self._Q_bits = None  # Register not defined by Q_bits
        a = np.array(a, dtype=complex)
        norm = np.linalg.norm(a)
        if abs(norm - 1) > 1e-6:
            print(f"The given amplitudes lead to a not normed state.\nbefore: {a}, norm = {norm}\nNormalizing...")
            a = a / norm
            print(f'after: {a}, norm = {np.linalg.norm(a)}')
        self._register = np.zeros(len(a), dtype=complex)
        for i in range(len(a)):
            self._register[i] = a[i]

    def write_abs_phase(self, absVal, phase):
        """Prepare register with given amplitudes and phases e.g. reg = amp0 exp(i phase0) |0> + amp1 exp(i phase1) |1>
        Attention! This will override the register. Use this only to prepare your Q-bits/register.

        Args:
            absVal (list of float): abs value for each component
            phase (list of int): Integer angle in deg for each component
        """
        assert (len(absVal) == 2 ** self._n)
        assert (np.all(np.imag(absVal) == 0))
        self._Q_bits = None  # Register not defined by Q_bits
        absVal = np.array(absVal)
        phase = np.array(phase)
        out = absVal * np.exp(1j * np.deg2rad(phase))
        print(f'absVal: {absVal}\nphase: {phase}\ncomplex: {out}')
        self.write_complex(out)

    def read(self, Q_bit=None, basis='c') -> int:
        """Read given Q-bit. If no Q-bit is given (Q_bit=None) all Q-bits are measured.

        Args:
            Q_bit (int, optional): Q-bit to read. Defaults to None.
            basis (char, optional): Basis in which measurement ist performed, c: comp. basis; y,x or z: bell basis; h: had; defaults to c

        Returns:
            np.array: Probabilities for for register/single Q-bit
        """
        # Set projector for POVM measurement
        if basis == 'c':
            proj = self._I
        elif basis == 'x':
            proj = self._X
        elif basis == 'y':
            proj = self._Y
        elif basis == 'z':
            proj = self._Z
        elif basis == 'h':
            proj = self._H
        else:
            # option: pass np.array as custom projective measurement, not documented yet
            print("Using custom projector for measurement.")
            proj = basis

        if Q_bit is None:
            # Measure all Q-bits
            if basis != 'c':
                # project all Q-bits with given projector, POVM Measurement
                self._operatorInBase(proj)
            prop = np.square(np.abs(self._register)).flatten()
            result = np.random.choice(a=2 ** self._n, p=prop)  # choice uses np.arange 0 to a, hence +1
            self.write_integer(result)
            out = format(result, '0b')
            # Add leading zeros
            if len(out) < self._n:
                out = '0' * (self._n - len(out)) + out
            msg = f"Measured state |{out}>."
        else:
            # Measuring one Q-bit
            # Measuring using projector to subspace
            if basis != 'c':
                # project all Q-bits with given projector, POVM Measurement
                self._operatorInBase(proj, Q_bit)
            # Prop for Q-bit i in |0> by projection using sp
            pro0 = [np.identity(2)] * self._n
            # Projective measurement -> POVM
            pro0[-Q_bit] = self._zero @ self._zero.T  # -Q-bit s.t. order of registers is correct
            pro0 = self._nKron(pro0)
            state0 = pro0 @ self._register
            p0 = np.linalg.norm(state0)
            # Prop for Q-bit i in |1> by projection using sp
            pro1 = [np.identity(2)] * self._n
            # Projective measurement -> POVM
            pro1[-Q_bit] = self._one @ self._one.T  # -Q-bit s.t. order of registers is correct
            pro1 = self._nKron(pro1)
            state1 = pro1 @ self._register
            p1 = np.linalg.norm(state1)
            # Check if state was normed
            assert (1 - p0 - p1 < 1e-6)
            # Project to new state
            result = np.random.choice(a=[0, 1], p=[p0 ** 2, p1 ** 2])
            state = state1 if result else state0  # True/False is alias for 1/0 in Python
            norm = p1 if result else p0
            # Normalize state
            self._register = state / norm
            msg = f"Measurement Q-bit {Q_bit:2d}: |{result:d}> \t (|0>: {p0 ** 2:2.2%} |1>: {p1 ** 2:2.2%})."
        print(msg)
        return msg

    # Set global Phase 0:
    def setGlobalPhase0(self):
        phase0 = np.angle(self._register[0])
        self._register[0] = np.abs(self._register[0])
        print(f'Phase |000>: {phase0}, {np.rad2deg(phase0)}')
        return self._operatorInBase(self._P(-phase0))  # NOTE: Das dreht die |1> Zustände

    # Methods to generate single Q-bit operators
    def had(self, Q_bit=None) -> np.array:
        """Applies the hadamard gate to Q-bit i.
        If no Q-bit is given (Q_bit=None) hadamard gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply HAD to. Defaults to None.

        Returns:
            np.array: Matrix for hadamard gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._H, Q_bit)

    def x(self, Q_bit=None) -> np.array:
        """Applies the Pauli-X gate to Q-bit i.
        If no Q-bit is given (Q_bit=None) NOT gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply NOT to. Defaults to None.

        Returns:
            np.array: Matrix for not gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._X, Q_bit)

    def y(self, Q_bit=None) -> np.array:
        """Applies the Pauli-Y gate to Q-bit i.
        If no Q-bit is given (Q_bit=None) Y gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply Y to. Defaults to None.

        Returns:
            np.array: Matrix for Y gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._Y, Q_bit)

    def z(self, Q_bit=None) -> np.array:
        """Applies the Pauli-Z (PHASE(180) gate to Q-bit i.
        If no Q-bit is given (Q_bit=None) NOT gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply Pauli-Z to. Defaults to None.

        Returns:
            np.array: Matrix for Pauli-Z gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._Z, Q_bit)

    def phase(self, angle: int, Q_bit=None):
        """Applies the PHASE gate with given angle (in deg)  to Q-bit i.
        If no Q-bit is given (Q_bit=None) PHASE(angle) gate will be applied to all Q-bits.

        Args:
            angle(int): Angle in deg
            Q_bit (int, optional): Q-bit to apply PHASE to. Defaults to None.

        Returns:
            np.array: Matrix for PHASE gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._P(np.deg2rad(angle)), Q_bit)

    def rx(self, angle: int, Q_bit=None):
        """Applies the Rx gate with given angle (in deg)  to Q-bit i.
        If no Q-bit is given (Q_bit=None) Rx(angle) gate will be applied to all Q-bits.

        Args:
            angle(int): Angle in deg
            Q_bit (int, optional): Q-bit to apply Rx to. Defaults to None.

        Returns:
            np.array: Matrix for Rx gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._Rx(np.deg2rad(angle)), Q_bit)

    def ry(self, angle: int, Q_bit=None):
        """Applies the Ry gate with given angle (in deg)  to Q-bit i.
        If no Q-bit is given (Q_bit=None) Ry(angle) gate will be applied to all Q-bits.

        Args:
            angle(int): Angle in deg
            Q_bit (int, optional): Q-bit to apply Ry to. Defaults to None.

        Returns:
            np.array: Matrix for Ry gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._Ry(np.deg2rad(angle)), Q_bit)

    def rz(self, angle: int, Q_bit=None):
        """Applies the Ry gate with given angle (in deg)  to Q-bit i.
        If no Q-bit is given (Q_bit=None) Rz(angle) gate will be applied to all Q-bits.

        Args:
            angle(int): Angle in deg
            Q_bit (int, optional): Q-bit to apply Rz to. Defaults to None.

        Returns:
            np.array: Matrix for Rz gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._Rz(np.deg2rad(angle)), Q_bit)

    # Aliases for ease of use and compatibility with QCEngine method names
    def qnot(self, Q_bit=None) -> np.array:
        """Applies the NOT gate to Q-bit i. Alias for qc_simulator.x(qbit)
        If no Q-bit is given (Q_bit=None) NOT gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply NOT to. Defaults to None.

        Returns:
            np.array: Matrix for not gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._X, Q_bit)

    def flip(self, Q_bit=None) -> np.array:
        """Applies the Pauli-Z (PHASE(180)) gate to Q-bit i. Alias for qc_simulator.z(qbit) and .phase(180, qbit)
        If no Q-bit is given (Q_bit=None) PHASE(90) gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply PHASE(90) to. Defaults to None.

        Returns:
            np.array: Matrix for PHASE(90) gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._P(np.deg2rad(90)), Q_bit)

    def s(self, Q_bit=None) -> np.array:
        """Applies the relative phase rotation by 90 deg to Q-bit i. Alias for qc_simulator.phase(90, qbit)
        If no Q-bit is given (Q_bit=None) PHASE(90) gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply PHASE(90) to. Defaults to None.

        Returns:
            np.array: Matrix for PHASE(90) gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._P(np.deg2rad(90)), Q_bit)

    def t(self, Q_bit=None) -> np.array:
        """Applies the relative phase rotation by 45 deg to Q-bit i. Alias for qc_simulator.phase(45, qbit)
        If no Q-bit is given (Q_bit=None) PHASE(45) gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply PHASE(45) to. Defaults to None.

        Returns:
            np.array: Matrix for PHASE(45) gate on given Q-bit in comp. basis.
        """
        # NOTE: Matrixform speichern. mit Phase gibt unschöne matrizen
        return self._operatorInBase(self._P(np.deg2rad(45)), Q_bit)

    # Root Gates
    def rootNot(self, Q_bit=None) -> np.array:
        """Applies the ROOT-NOT (ROOT-X) gate to Q-bit i.
        If no Q-bit is given (Q_bit=None) ROOT-NOT gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply ROOT-NOT to. Defaults to None.

        Returns:
            np.array: Matrix for ROOT-NOT gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._ROOTX, Q_bit)

    def rootZ(self, Q_bit=None) -> np.array:
        """Applies the ROOT-Z gate to Q-bit i.
        If no Q-bit is given (Q_bit=None) ROOT-Z gate will be applied to all Q-bits.

        Args:
            Q_bit (int, optional): Q-bit to apply ROOT-Z to. Defaults to None.

        Returns:
            np.array: Matrix for ROOT-Z gate on given Q-bit in comp. basis.
        """
        return self._operatorInBase(self._ROOTZ, Q_bit)

    def swap(self, i: int, j: int) -> np.array:
        """Performs SWAP operation with given Q-bits i and j.

        Args:
            i (int): Q-bit to be swapped.
            j (int): Q-bit to be swapped.

        Returns:
            np.array: Matrix representation for used SWAP gate in comp. basis.
        """
        # SWAP by using CNOT gates
        cn1 = self.cNot(i, j)
        cn2 = self.cNot(j, i)
        return cn1 @ cn2 @ cn1

    # Methods to generate multi Q-bit operators
    def cHad(self, control_Q_bit: int, not_Q_bit: int) -> np.array:
        """Applies the controlled Hadamard gate with given control and target Q-bit.

        Args:
            control_Q_bit (int or list): Q-bit(s) which is controlling.
            not_Q_bit (int): Q-bit on which Hadamard gate shall be applied.

        Returns:
            np.array: controlled Hadamard gate for given parameters in comp. basis.
        """
        return self._controlledU(self._H, control_Q_bit, not_Q_bit)

    def cNot(self, control_Q_bit: int, not_Q_bit: int) -> np.array:
        """Applies the CNOT gate with given control and target Q-bit.

        Args:
            control_Q_bit (int or list): Q-bit(s) which is controlling.
            not_Q_bit (int): Q-bit on which Not gate shall be applied.

        Returns:
            np.array: c_not gate for given parameters in comp. basis.
        """
        return self._controlledU(self._X, control_Q_bit, not_Q_bit)

    def ccNot(self, control_Q_bit1: int, control_Q_bit2: int, not_Q_bit: int) -> np.array:
        """Applies the CCNOT gate with given control and target Q-bit.

        Args:
            control_Q_bit (int): Q-bit which is controlling.
            not_Q_bit (int): Q-bit on which Not gate shall be applied.

        Returns:
            np.array: cc_not gate for given parameters in comp. basis.
        """
        return self._controlledU(self._X, [control_Q_bit1, control_Q_bit2], not_Q_bit)

    def cPhase(self, control_Q_bit: int, target_Q_bit: int, angle: int) -> np.array:
        """Applies the CPHASE gate with given angle, given control and target Q-bit.

        Args:
            control_reg (int): Q-bit which is controlling.
            target_Q_bit (int): Q-bit on which Phase gate shall be applied.
            angle (int): Angle in deg for rotation.

        Returns:
            np.array: CPHASE gate for given parameters in comp. basis.
        """
        return self._controlledU(self._P(np.deg2rad(angle)), control_Q_bit, target_Q_bit)

    def cRx(self, control_Q_bit: int, target_Q_bit: int, angle: int) -> np.array:
        """Applies the controlled Rx gate with given angle, given control and target Q-bit.

        Args:
            control_reg (int): Q-bit which is controlling.
            target_Q_bit (int): Q-bit on which Rx gate shall be applied.
            angle (int): Angle in deg for rotation.

        Returns:
            np.array: controlled Rx gate for given parameters in comp. basis.
        """
        return self._controlledU(self._Rx(np.deg2rad(angle)), control_Q_bit, target_Q_bit)

    def cRy(self, control_Q_bit: int, target_Q_bit: int, angle: int) -> np.array:
        """Applies the controlled Rx gate with given angle, given control and target Q-bit.

        Args:
            control_reg (int): Q-bit which is controlling.
            target_Q_bit (int): Q-bit on which Ry gate shall be applied.
            angle (int): Angle in deg for rotation.

        Returns:
            np.array: controlled Ry gate for given parameters in comp. basis.
        """
        return self._controlledU(self._Ry(np.deg2rad(angle)), control_Q_bit, target_Q_bit)

    def cRz(self, control_Q_bit: int, target_Q_bit: int, angle: int) -> np.array:
        """Applies the controlled Rz gate with given angle, given control and target Q-bit.

        Args:
            control_reg (int): Q-bit which is controlling.
            target_Q_bit (int): Q-bit on which Rz gate shall be applied.
            angle (int): Angle in deg for rotation.

        Returns:
            np.array: controlled Rz gate for given parameters in comp. basis.
        """
        return self._controlledU(self._Rz(np.deg2rad(angle)), control_Q_bit, target_Q_bit)

    def cZ(self, control_Q_bit: int, not_Q_bit: int) -> np.array:
        """Applies the CZ gate with given control and target Q-bit.

        Args:
            control_Q_bit (int or list): Q-bit(s) which is controlling.
            not_Q_bit (int): Q-bit on which Z gate shall be applied.

        Returns:
            np.array: CZ gate for given parameters in comp. basis.
        """
        return self._controlledU(self._Z, control_Q_bit, not_Q_bit)

    def cSwap(self, control_Q_bit: int, i: int, j: int) -> np.array:
        """Performs CSWAP operation with given Q-bits i and j controlled by given control Q-bit

        Args:
            control_Q_bit (int or list): control Q-bit(s).
            i (int): registers to be swapped.
            j (int): registers to be swapped.

        Returns:
            np.array: Matrix representation for used CSWAP gate in comp. basis.
        """
        # CSWAP by using CCNOT gates TODO: 1 sparen
        c1 = [i]
        c1.extend(control_Q_bit)
        c2 = [j]
        c2.extend(control_Q_bit)
        ccn1 = self.cNot(c1, j)
        ccn2 = self.cNot(c2, i)
        return ccn1 @ ccn2 @ ccn1

    # Private/hidden methods
    def _getBasisVector(self, i: int) -> np.array:
        """Returns i-th basis (row)-vector for dimensions n (comp. basis)

        Args:
            i (int): number of basis vector

        Returns:
            np.array: i-th basis vector (row vector)
        """
        return self._basis[:, i, None]

    def _nKron(self, ops_to_kron) -> np.array:
        """Helper function to apply cascade kroneker products in list

        Args:
            ops_to_kron (list[np.array]): list of matrices to apply in kroneker products

        Returns:
            np.array: Result
        """
        result = 1
        for i in ops_to_kron:
            result = np.kron(result, i)
        return result

    def _operatorInBase(self, operator: np.array, Q_bit=None) -> np.array:
        """Applies given operator U to given Q-bit and returns the matrix representation in comp. basis.
        If no Q-bit is specified (Q_bit=None) U is applied to all Q-bits.

        Args:
            operator (np.array): Operator U.
            Q-bit (int, optional): Q-Bit on which operator should apply. Defaults to None.

        Returns:
            np.array: Operator U applied to Q-bit in comp. basis.
        """
        if Q_bit is None:
            some_list = [operator] * self._n
        else:
            if type(Q_bit) == list:
                assert (len(Q_bit) > 0)
            Q_bit = np.array(Q_bit, dtype=int)
            assert (np.all(Q_bit > 0))
            assert (np.all(Q_bit <= self._n))
            some_list = np.array([np.identity(2)] * self._n, dtype=complex)
            some_list[-Q_bit] = operator  # -Q-bit s.t. order of registers is correct
        op = self._nKron(some_list)
        self._register = op @ self._register
        return op

    def _controlledU(self, operator: np.array, control_Q_bit: int, target_Q_bit: int) -> np.array:
        """Returns controlled version of given operator gate

        Args:
            operator (np.array): Matrix form of operator U.
            control_Q_bit (int or list(int)): Controlling Q-bit(s).
            target_Q_bit (int): Q-bit to apply operator to.

        Returns:
            np.array: Matrix for controlled operator in comp. basis.
        """
        control_Q_bit = np.array(control_Q_bit, dtype=int)
        assert (np.all(target_Q_bit != control_Q_bit))

        control0 = np.array([np.identity(2)] * self._n, dtype=complex)
        control0[-control_Q_bit] = np.array([[1, 0], [0, 0]])  # |0><0| check if |0>, apply I if so

        control1 = np.array([np.identity(2)] * self._n, dtype=complex)
        control1[-control_Q_bit] = np.array([[0, 0], [0, 1]])  # |1><1| check if |1>
        control1[-target_Q_bit] = operator  # apply U if so
        op = self._nKron(control0) + self._nKron(control1)
        self._register = op @ self._register
        return op