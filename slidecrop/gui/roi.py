from PyQt5 import QtCore, QtGui, QtWidgets


class ROITable(QtWidgets.QWidget):
    """
    GUI element holding information of regions segmented from 
    low resolution image stored in slide scanner image
    """

    def __init__(self, parent=None, table_widget=None):

        super(ROITable, self).__init__(table_widget)
        self.parent = parent
        self.table_widget = table_widget
        # self.table_widget.setSizeAdjustPolicy(
        #     QtWidgets.QAbstractScrollArea.AdjustToContents
        # )
        self.table_widget.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table_widget.clicked.connect(self.item_selected)
        self._rows = []

    def update(self, roi_list):
        """
        Update (redraw) the table widget
        """
        if roi_list:
            self.table_widget.clear()
            self.table_widget.setRowCount(len(roi_list))
            self.table_widget.setColumnCount(5)
            self.table_widget.setHorizontalHeaderLabels(["", "x", "y", "w", "h"]) 
            header = self.table_widget.horizontalHeader()
            for c in range(0, 5):
                header.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeToContents)

            for rid, roi in enumerate(roi_list):
                chk_box_item = QtWidgets.QTableWidgetItem()
                chk_box_item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chk_box_item.setCheckState(QtCore.Qt.Checked)
                self.table_widget.setItem(rid, 0, chk_box_item)

                rect = roi.rect()
                x = QtWidgets.QTableWidgetItem("{}".format(int(rect.x())))
                self.table_widget.setItem(rid, 1, x)
                y = QtWidgets.QTableWidgetItem("{}".format(int(rect.y())))
                self.table_widget.setItem(rid, 2, y)
                w = QtWidgets.QTableWidgetItem("{}".format(int(rect.width())))
                self.table_widget.setItem(rid, 3, w)
                h = QtWidgets.QTableWidgetItem("{}".format(int(rect.height())))
                self.table_widget.setItem(rid, 4, h)

    def item_selected(self, id):
        """
        Responds to a row being selected by mouse click
        """
        r = id.row()
        row = []
        for c in range(1, 5):
            item = self.table_widget.item(r, c)
            row.append(int(item.text()))

        # roi = ROIItem(QtCore.QRectF(*row))
        # roi.setSelected(True)
        # # self.parent.viewer.clear_scene()
        # self.parent.viewer.addROI(roi)
        self.parent.viewer.deselectROIs()
        transform = self.parent.viewer.transform()
        scene = self.parent.viewer._scene
        roi = scene.itemAt(QtCore.QPointF(row[0], row[1]), transform)
        roi.setSelected(True)

    def get_rows(self):
        """
        :returns all table rows
        """
        rows = []
        for r in range(self.table_widget.rowCount()):
            row = []
            for c in range(1, self.table_widget.columnCount()):
                row.append(int(self.table_widget.item(r, c).text()))
            rows.append(row)
        return rows

    def get_checked_rows(self):
        """
        Return the numbers of the rows that are checked.
        To be used to select which scaled ROIs will be cropped.
        """
        rows = []
        for r in range(self.table_widget.rowCount()):
            chk_box_item = self.table_widget.item(r, 0)
            if chk_box_item.checkState() == 2:
                rows.append(r)
        return rows


class RubberBand(QtWidgets.QRubberBand):
    def __init__(self, parent):
        super(RubberBand, self).__init__(QtWidgets.QRubberBand.Rectangle, parent)
        pal = QtGui.QPalette()
        pal.setBrush(QtGui.QPalette.Highlight, QtGui.QBrush(QtCore.Qt.yellow))
        self.setPalette(pal)  


class ROIItem(QtWidgets.QGraphicsRectItem):

    handleTopLeft = 1
    handleTopMiddle = 2
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    handleSize = +8.0
    handleSpace = -4.0

    handleCursors = {
        handleTopLeft: QtCore.Qt.SizeFDiagCursor,
        handleTopMiddle: QtCore.Qt.SizeVerCursor,
        handleTopRight: QtCore.Qt.SizeBDiagCursor,
        handleMiddleLeft: QtCore.Qt.SizeHorCursor,
        handleMiddleRight: QtCore.Qt.SizeHorCursor,
        handleBottomLeft: QtCore.Qt.SizeBDiagCursor,
        handleBottomMiddle: QtCore.Qt.SizeVerCursor,
        handleBottomRight: QtCore.Qt.SizeFDiagCursor,
    }

    def __init__(self, parent, *args):
        """
        Initialize the shape.
        """
        super().__init__(*args)
        self.parent = parent
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
        self.updateHandlesPos()

    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = QtCore.Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.setCursor(QtCore.Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()

        rect = self.rect()
        roi = [rect.x(), rect.y(), rect.width(), rect.height()]
        rows = self.parent.roi_table.get_rows()
        row_id = rows.index(roi)
        self.parent.roi_table.table_widget.selectRow(row_id)
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()

    def boundingRect(self):
        """
        Returns the bounding rect of the shape (including the resize handles).
        """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft] = QtCore.QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle] = QtCore.QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight] = QtCore.QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QtCore.QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight] = QtCore.QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft] = QtCore.QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QtCore.QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QtCore.QRectF(b.right() - s, b.bottom() - s, s, s)

    def interactiveResize(self, mousePos):
        """
        Perform shape interactive resize.
        """
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()
        diff = QtCore.QPointF(0, 0)

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTopLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleTopMiddle:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleTopRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleMiddleLeft:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleMiddleRight:
            print("MR")
            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomMiddle:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        self.updateHandlesPos()

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        """
        path = QtGui.QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        """
        # painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 2.0, QtCore.Qt.SolidLine))
        painter.drawRect(self.rect())

        if self.isSelected():
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 255)))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0, 255), 2.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)