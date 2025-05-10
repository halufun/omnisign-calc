#!/usr/bin/env python3
import sys, math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QGridLayout, QMessageBox, QInputDialog
)

# initialize application and sign symbols
app = QApplication(sys.argv)
app.sign_symbols = ['+']  # start with single sign (unsigned)

class SignedNumber:
    __slots__ = ('mag', 's')
    def __init__(self, mag: float, s: int = 0):
        if mag < 0:
            raise ValueError("Magnitude must be ≥ 0")
        # force unsigned if only one symbol
        if len(app.sign_symbols) == 1:
            s = 0
        elif s < 0 or s >= len(app.sign_symbols):
            raise ValueError(f"Sign index must be between 0 and {len(app.sign_symbols)-1}")
        self.mag = mag
        self.s = s

    def __repr__(self):
        val = f"{self.mag:.6g}"  # up to 6 significant digits
        if len(app.sign_symbols) == 1:
            return val
        return f"{app.sign_symbols[self.s]}{val}"

# arithmetic operations support float mags
def add(a: SignedNumber, b: SignedNumber) -> SignedNumber:
    if len(app.sign_symbols) == 1:
        return SignedNumber(a.mag + b.mag)
    if a.s == b.s:
        return SignedNumber(a.mag + b.mag, a.s)
    # opposite signs: subtract magnitudes
    if a.mag >= b.mag:
        return SignedNumber(a.mag - b.mag, a.s)
    return SignedNumber(b.mag - a.mag, b.s)

def sub(a: SignedNumber, b: SignedNumber) -> SignedNumber:
    if len(app.sign_symbols) == 1:
        return SignedNumber(a.mag - b.mag)
    neg_b = SignedNumber(b.mag, (b.s + 1) % len(app.sign_symbols))
    return add(a, neg_b)

def mult(a: SignedNumber, b: SignedNumber) -> SignedNumber:
    if len(app.sign_symbols) == 1:
        return SignedNumber(a.mag * b.mag)
    return SignedNumber(a.mag * b.mag, (a.s + b.s) % len(app.sign_symbols))

def div(a: SignedNumber, b: SignedNumber) -> SignedNumber:
    if b.mag == 0:
        raise ZeroDivisionError("Division by zero")
    if len(app.sign_symbols) == 1:
        return SignedNumber(a.mag / b.mag)
    return SignedNumber(a.mag / b.mag, (a.s - b.s) % len(app.sign_symbols))

def exp_op(a: SignedNumber, b: SignedNumber) -> SignedNumber:
    k = b.mag
    if len(app.sign_symbols) == 1:
        return SignedNumber(math.pow(a.mag, k))
    return SignedNumber(math.pow(a.mag, k), (a.s * int(k)) % len(app.sign_symbols))

def root_op(a: SignedNumber, b: SignedNumber) -> SignedNumber:
    k = b.mag
    if k == 0:
        raise ValueError("Root degree must be non-zero")
    root = a.mag ** (1.0 / k)
    if len(app.sign_symbols) == 1:
        return SignedNumber(root)
    # sign: odd root preserves sign, even root only for unsigned or positive
    if k % 2 == 1:
        s_prime = a.s
    else:
        if a.s != 0:
            raise ValueError("Even root of negative is not defined")
        s_prime = 0
    return SignedNumber(root, s_prime)

class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("omnisigned calculator")
        layout = QGridLayout()

        # Factor A
        layout.addWidget(QLabel("A:"), 0, 0)
        self.a_mag = QLineEdit("0")
        self.a_sign = QComboBox()
        self.a_sign.addItems(app.sign_symbols)
        layout.addWidget(self.a_mag, 0, 1)
        layout.addWidget(self.a_sign, 0, 2)

        # Factor B
        layout.addWidget(QLabel("B:"), 1, 0)
        self.b_mag = QLineEdit("0")
        self.b_sign = QComboBox()
        self.b_sign.addItems(app.sign_symbols)
        layout.addWidget(self.b_mag, 1, 1)
        layout.addWidget(self.b_sign, 1, 2)

        # Operation selection
        layout.addWidget(QLabel("Operation:"), 2, 0)
        self.op_combo = QComboBox()
        self.operations = {
            'Add': add, 'Sub': sub,
            'Mul': mult, 'Div': div,
            'Pow': exp_op, 'Root': root_op
        }
        self.op_combo.addItems(self.operations.keys())
        layout.addWidget(self.op_combo, 2, 1, 1, 2)

        # Add/Remove sign buttons
        self.add_sign_btn = QPushButton("Add Sign")
        self.add_sign_btn.clicked.connect(self.add_sign)
        self.remove_sign_btn = QPushButton("Remove Sign")
        self.remove_sign_btn.clicked.connect(self.remove_sign)
        layout.addWidget(self.add_sign_btn, 3, 0)
        layout.addWidget(self.remove_sign_btn, 3, 1)

        # Compute button
        compute_btn = QPushButton("Compute")
        compute_btn.clicked.connect(self.compute)
        layout.addWidget(compute_btn, 4, 0, 1, 3)

        # Result
        layout.addWidget(QLabel("Result:"), 5, 0)
        self.result = QLabel("")
        layout.addWidget(self.result, 5, 1, 1, 2)

        self.setLayout(layout)
        self.update_ui()

    def update_ui(self):
        single = len(app.sign_symbols) == 1
        self.a_sign.setEnabled(not single)
        self.b_sign.setEnabled(not single)
        self.remove_sign_btn.setEnabled(not single)

    def add_sign(self):
        text, ok = QInputDialog.getText(self, 'New Sign', 'Enter new sign symbol:')
        if ok and text:
            symbol = text.strip()[0]
            if symbol in app.sign_symbols:
                QMessageBox.information(self, 'Info', 'Sign already exists.')
                return
            app.sign_symbols.append(symbol)
            self.a_sign.addItem(symbol)
            self.b_sign.addItem(symbol)
            self.update_ui()

    def remove_sign(self):
        if len(app.sign_symbols) > 1:
            app.sign_symbols.pop()
            self.a_sign.removeItem(self.a_sign.count()-1)
            self.b_sign.removeItem(self.b_sign.count()-1)
            self.update_ui()

    def compute(self):
        try:
            a_val = float(self.a_mag.text())
            b_val = float(self.b_mag.text())
            a = SignedNumber(a_val, self.a_sign.currentIndex())
            b = SignedNumber(b_val, self.b_sign.currentIndex())
            fn = self.operations[self.op_combo.currentText()]
            res = fn(a, b)
            self.result.setText(repr(res))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == '__main__':
    win = Calculator()
    win.show()
    sys.exit(app.exec_())
