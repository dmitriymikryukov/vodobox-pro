from PyQt5.QtWidgets import QWidget, QButtonGroup
from PyQt5.QtCore import pyqtSignal
from ui.converted.gen_service_menu_window import Ui_Form


class ServiceMenuWindow(QWidget):
    service_menu_exited = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # object instances
        self.service_menu_btn_group = QButtonGroup()
        self.maintenance_btn_group = QButtonGroup()

        # customization
        for i, service_menu_btn in enumerate([
            self.ui.maintenance_btn,
            self.ui.test_mode_btn,
            self.ui.diagnostics_btn,
            self.ui.system_control_btn,
            self.ui.parameter_settings_btn,
        ]):
            self.service_menu_btn_group.addButton(service_menu_btn, i)

        for i, maintenance_menu_btn in enumerate([
            self.ui.refill_btn,
            self.ui.adding_product_btn,
            self.ui.encashment_btn,
            self.ui.adding_coins_btn,
            self.ui.washing_btn,
        ]):
            self.maintenance_btn_group.addButton(maintenance_menu_btn, i)

        self.ui.increase_btn.hide()
        self.ui.decrease_btn.hide()

        sp_retain = self.ui.confirm_btn.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.ui.confirm_btn.setSizePolicy(sp_retain)
        self.ui.down_btn.setSizePolicy(sp_retain)

        # signals
        self.ui.exit_btn.clicked.connect(self.exit_handler)

        self.ui.up_btn.clicked.connect(self.select_up_handler)
        self.ui.down_btn.clicked.connect(self.select_down_handler)

        self.ui.confirm_btn.clicked.connect(self.confirm_handler)
        self.ui.diagnostic_back_btn.clicked.connect(self.switch_on_service_menu)

    def exit_handler(self):
        current_service_page = self.ui.stack_widget.currentWidget()
        match current_service_page:
            case self.ui.service_menu_page:
                self.service_menu_exited.emit()
            case self.ui.maintenance_page:
                current_maintenance_page = self.ui.maintenance_stack_widget.currentWidget()
                if current_maintenance_page is self.ui.maintenance_index_page:
                    self.switch_on_service_menu()
                else:
                    self.switch_on_maintenance()

    def confirm_handler(self):
        current_service_page = self.ui.stack_widget.currentWidget()
        match current_service_page:
            case self.ui.service_menu_page:
                check_id = self.service_menu_btn_group.checkedId()
                match check_id:
                    case 0:
                        self.switch_on_maintenance()
                    case 1:
                        self.switch_on_test_mode()
                    case 2:
                        self.switch_on_diagnostics()
                    case 3:
                        self.switch_on_system_control()
                    case 4:
                        self.switch_on_parameter_settings()

            case self.ui.maintenance_page:
                check_id = self.maintenance_btn_group.checkedId()
                match check_id:
                    case 0:
                        self.switch_on_refill()
                    case 1:
                        self.switch_on_adding_product()
                    case 2:
                        self.switch_on_encashment()
                    case 3:
                        self.switch_on_adding_coins()
                    case 4:
                        self.switch_on_washing()

    def select_up_handler(self):
        current_service_page = self.ui.stack_widget.currentWidget()
        match current_service_page:
            case self.ui.service_menu_page:
                self.select_menu_up(self.service_menu_btn_group)
            case self.ui.maintenance_page:
                current_maintenance_page = self.ui.maintenance_stack_widget.currentWidget()
                match current_maintenance_page:
                    case self.ui.maintenance_index_page:
                        self.select_menu_up(self.maintenance_btn_group)
                    case self.ui.adding_product_page:
                        pass
                    case self.ui.encashment_page:
                        pass
                    case self.ui.adding_coins_page:
                        pass

    def select_down_handler(self):
        current_service_page = self.ui.stack_widget.currentWidget()
        match current_service_page:
            case self.ui.service_menu_page:
                self.select_menu_down(self.service_menu_btn_group)
            case self.ui.maintenance_page:
                current_maintenance_page = self.ui.maintenance_stack_widget.currentWidget()
                match current_maintenance_page:
                    case self.ui.maintenance_index_page:
                        self.select_menu_down(self.maintenance_btn_group)
                    case self.ui.adding_product_page:
                        pass
                    case self.ui.encashment_page:
                        pass
                    case self.ui.adding_coins_page:
                        pass

    def select_menu_up(self, btn_group: QButtonGroup):
        check_id = btn_group.checkedId()
        if check_id == -1:
            btn_group.buttons()[0].setChecked(True)
        else:
            btn_group.buttons()[
                check_id - 1
            ].setChecked(True)

    def select_menu_down(self, btn_group: QButtonGroup):
        check_id = btn_group.checkedId()
        if check_id == -1:
            btn_group.buttons()[0].setChecked(True)
        else:
            try:
                btn_group.buttons()[
                    check_id + 1
                    ].setChecked(True)
            except IndexError:
                btn_group.buttons()[0].setChecked(True)

    # switch methods for service menu
    def switch_on_service_menu(self):
        # прячем кнопки
        self.ui.top_left_stack.setCurrentWidget(self.ui.empty_page)
        self.ui.second_top_left_stack.setCurrentWidget(self.ui.empty_page_2)
        self.ui.top_right_stack.setCurrentWidget(self.ui.empty_page_3)
        self.ui.second_top_right_stack.setCurrentWidget(self.ui.empty_page_4)

        # отрисовываем кнопки
        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.service_exit_page)
        self.ui.bottom_left_stack.setCurrentWidget(self.ui.confirm_page)
        self.ui.second_bottom_right_stack.setCurrentWidget(self.ui.up_page)
        self.ui.bottom_right_stack.setCurrentWidget(self.ui.down_page)

        # меняем на нужные виджеты для сервисного меню
        self.ui.top_lbl_stack_widget.setCurrentWidget(self.ui.service_menu_lbl_page)
        self.ui.stack_widget.setCurrentWidget(self.ui.service_menu_page)
        self.ui.bottom_info_stack_widget.setCurrentWidget(self.ui.product_info_page)

    def switch_on_maintenance(self):
        # прячем кнопки
        self.ui.decrease_btn.hide()
        self.ui.increase_btn.hide()

        # отрисовываем кнопки
        self.ui.confirm_btn.show()
        self.ui.open_door_btn.show()
        self.ui.up_btn.show()
        self.ui.down_btn.show()

        # меняем на нужные виджеты для меню обслуживания
        self.ui.top_lbl_stack_widget.setCurrentWidget(self.ui.maintenance_lbl_page)
        self.ui.top_lbl_maintenance_stack_widget.setCurrentWidget(self.ui.maintenance_index_lbl_page)

        self.ui.stack_widget.setCurrentWidget(self.ui.maintenance_page)
        self.ui.maintenance_stack_widget.setCurrentWidget(self.ui.maintenance_index_page)

        self.ui.bottom_info_stack_widget.setCurrentWidget(self.ui.product_info_page)

    def switch_on_test_mode(self):
        pass

    def switch_on_diagnostics(self):
        self.ui.top_lbl_stack_widget.setCurrentWidget(self.ui.diagnostic_lbl_page)
        self.ui.stack_widget.setCurrentWidget(self.ui.diagnostic_main_info_page)
        self.ui.bottom_info_stack_widget.setCurrentWidget(self.ui.diagnostic_page)

        self.ui.top_left_stack.setCurrentWidget(self.ui.diagnostic_top_left_page)
        self.ui.second_top_left_stack.setCurrentWidget(self.ui.second_top_left_diagnostic_page)

        self.ui.second_bottom_left_stack.setCurrentWidget(self.ui.diagnostic_back_page)
        self.ui.bottom_left_stack.setCurrentWidget(self.ui.bottom_left_diagnostic_page)

        self.ui.top_right_stack.setCurrentWidget(self.ui.diagnostic_top_right_page)
        self.ui.second_top_right_stack.setCurrentWidget(self.ui.diagnostic_second_top_right_page)

        self.ui.second_bottom_right_stack.setCurrentWidget(self.ui.second_bottom_right_diagnostic_page)
        self.ui.bottom_right_stack.setCurrentWidget(self.ui.bottom_right_diagnostic_page)

    def switch_on_system_control(self):
        pass

    def switch_on_parameter_settings(self):
        pass

    # switch methods for maintenance menu
    def switch_on_refill(self):
        pass

    def switch_on_adding_product(self):
        # прячем кнопки
        self.ui.confirm_btn.hide()
        self.ui.open_door_btn.hide()

        # отрисовываем кнопки
        self.ui.increase_btn.show()
        self.ui.decrease_btn.show()

        # меняем на нужные виджеты для добавления товара
        self.ui.top_lbl_maintenance_stack_widget.setCurrentWidget(self.ui.adding_product_lbl_page)
        self.ui.maintenance_stack_widget.setCurrentWidget(self.ui.adding_product_page)
        self.ui.bottom_info_stack_widget.setCurrentWidget(self.ui.save_attention_page)

    def switch_on_encashment(self):
        # прячем кнопки
        self.ui.increase_btn.hide()
        self.ui.decrease_btn.hide()
        self.ui.confirm_btn.hide()
        self.ui.open_door_btn.hide()

        # меняем на нужные виджеты для инкассации
        self.ui.top_lbl_maintenance_stack_widget.setCurrentWidget(self.ui.encashment_lbl_page)
        self.ui.maintenance_stack_widget.setCurrentWidget(self.ui.encashment_page)
        self.ui.bottom_info_stack_widget.setCurrentWidget(self.ui.cash_page)

    def switch_on_adding_coins(self):
        # прячем кнопки
        self.ui.increase_btn.hide()
        self.ui.decrease_btn.hide()
        self.ui.confirm_btn.hide()
        self.ui.open_door_btn.hide()
        self.ui.up_btn.hide()
        self.ui.down_btn.hide()

        # меняем на нужные виджеты для пополнения монет
        self.ui.top_lbl_maintenance_stack_widget.setCurrentWidget(self.ui.coins_adding_lbl_page)
        self.ui.maintenance_stack_widget.setCurrentWidget(self.ui.adding_coins_page)
        self.ui.bottom_info_stack_widget.setCurrentWidget(self.ui.cash_page)

    def switch_on_washing(self):
        pass
