import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem, \
    QGraphicsTextItem, QGraphicsItem, QPushButton, QMessageBox, QGraphicsProxyWidget, QLabel
from PyQt5.QtGui import QPainter, QPen, QBrush, QMouseEvent, QWheelEvent
from PyQt5.QtCore import Qt, QPointF, pyqtSlot

# Constants
ROLE_COLORS = {
    "PM": "blue",
    "GC": "green",
    "Foreman": "yellow",
    "Electrician": "red"
}
JOB_HUB_WIDTH = 300
JOB_HUB_HEIGHT = 400
BOX_HEIGHT = 30
ELECTRICIAN_BOX_HEIGHT = 100
JOB_HUB_HEIGHT_COLLAPSED = 200

class Canvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setScene(QGraphicsScene(self))
        self.scale_factor = 1.0
        self._panning = False
        self._start_pos = QPointF()
        self.mousepos = QPointF()

        # Disable default drag mode
        self.setDragMode(QGraphicsView.NoDrag)

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.scale(factor, factor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._start_pos = self.mapToScene(event.pos())
            self.setCursor(Qt.ClosedHandCursor)
            self._panning = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = self.mapToScene(event.pos()) - self._start_pos
            self._start_pos = self.mapToScene(event.pos())
            self.setSceneRect(self.sceneRect().translated(-delta.x(), -delta.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ArrowCursor)
            self._panning = False
        super().mouseReleaseEvent(event)

class JobSiteHub(QGraphicsRectItem):
    def __init__(self, x, y, text, address="", parent=None, scene=None):
        super().__init__(0, 0, JOB_HUB_WIDTH, JOB_HUB_HEIGHT, parent)
        self.setPos(x, y)
        self.text = text
        self.address = address
        self.collapsed = False

        self.setBrush(QBrush(Qt.lightGray))

        # Text
        self.text_item = QGraphicsTextItem(self.get_display_text(), self)
        self.text_item.setPos(JOB_HUB_WIDTH / 2 - self.text_item.boundingRect().width() / 2, -20)

        # Erase button
        self.erase_button = QGraphicsTextItem("X", self)
        self.erase_button.setDefaultTextColor(Qt.red)
        self.erase_button.setPos(JOB_HUB_WIDTH - 15, 15)
        self.erase_button.setFlag(QGraphicsItem.ItemIsSelectable)

        # Snap boxes
        self.pm_box = self.create_snap_box()
        self.gc_box = self.create_snap_box()
        self.foreman_box = self.create_snap_box()

        # Electrician button
        self.electrician_button = QPushButton("Electricians", None)
        self.electrician_button.clicked.connect(self.show_electrician_profile)
        self.electrician_proxy = self.create_proxy(self.electrician_button, 10, JOB_HUB_HEIGHT - 40, scene)

        # Collapse button
        self.collapse_button = QGraphicsTextItem("[-]", self)
        self.collapse_button.setPos(15, JOB_HUB_HEIGHT - 15)
        self.collapse_button.setFlag(QGraphicsItem.ItemIsSelectable)

        self.pm_occupied = False
        self.gc_occupied = False
        self.foreman_occupied = False
        self.electrician_occupied = []

        self.update_positions()

    def create_proxy(self, widget, x, y, scene):
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(x, y)
        scene.addItem(proxy)
        return proxy

    def get_display_text(self):
        return f"{self.text}\n{self.address}"

    def create_snap_box(self):
        snap_box = QGraphicsRectItem(0, 0, JOB_HUB_WIDTH - 20, BOX_HEIGHT, self)
        snap_box.setBrush(QBrush(Qt.white))
        snap_box.setPen(QPen(Qt.black))
        return snap_box

    def update_positions(self):
        self.pm_box.setRect(10, 10, JOB_HUB_WIDTH - 20, BOX_HEIGHT)
        self.gc_box.setRect(10, 20 + BOX_HEIGHT, JOB_HUB_WIDTH - 20, BOX_HEIGHT)
        self.foreman_box.setRect(10, 30 + 2 * BOX_HEIGHT, JOB_HUB_WIDTH - 20, BOX_HEIGHT)

        if not self.collapsed:
            self.electrician_proxy.setPos(10, JOB_HUB_HEIGHT - 40)
            self.collapse_button.setPlainText("[-]")
        else:
            self.electrician_proxy.setPos(10, JOB_HUB_HEIGHT_COLLAPSED - 40)
            self.collapse_button.setPlainText("[+]")

        self.collapse_button.setPos(15, JOB_HUB_HEIGHT - 15)
        self.erase_button.setPos(JOB_HUB_WIDTH - 15, 15)

    def mousePressEvent(self, event):
        if self.erase_button.isUnderMouse():
            self.confirm_erase_hub()
        elif self.collapse_button.isUnderMouse():
            self.toggle_electrician_box()
        super().mousePressEvent(event)

    def toggle_electrician_box(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.setRect(0, 0, JOB_HUB_WIDTH, JOB_HUB_HEIGHT_COLLAPSED)
        else:
            self.setRect(0, 0, JOB_HUB_WIDTH, JOB_HUB_HEIGHT)
        self.update_positions()

    def confirm_erase_hub(self):
        result = QMessageBox.question(None, "Delete Job Hub", "Are you sure you want to delete this job hub?", QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            self.erase_hub()

    def erase_hub(self):
        self.scene().removeItem(self)

    def show_electrician_profile(self):
        QMessageBox.information(None, "Electrician Profile", "Electrician profile details here.")

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        # Assuming the event contains the employee ID or reference
        employee_id = event.mimeData().text()
        if employee_id not in self.electrician_occupied:
            self.electrician_occupied.append(employee_id)
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Job Site Hub Application")
        self.setGeometry(100, 100, 800, 600)

        self.view = Canvas(self)
        self.setCentralWidget(self.view)

        hub = JobSiteHub(100, 100, "Job Site 1", "123 Main St", scene=self.view.scene())
        self.view.scene().addItem(hub)

        # Create a label for zooming workaround
        self.label = QLabel('Hello world', self)
        self.font_size = 30
        self.label.setStyleSheet(f'color: red; font-size: {self.font_size}px')
        self.label.adjustSize()
        self.view.scene().addWidget(self.label)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    @pyqtSlot()
    def zoom_in(self):
        self.font_size = min(1000, self.font_size + 1)
        self.label.setStyleSheet(f'color: red; font-size: {self.font_size}px')
        self.label.adjustSize()

    @pyqtSlot()
    def zoom_out(self):
        self.font_size = max(2, self.font_size - 1)
        self.label.setStyleSheet(f'color: red; font-size: {self.font_size}px')
        self.label.adjustSize()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
