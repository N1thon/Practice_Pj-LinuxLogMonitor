import paramiko
import re
import time
from PyQt5 import QtWidgets, QtCore
from UI.ui import Ui_Form
import geoip2.database
import os
import threading


class MainWindow(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.update_timer_1 = QtCore.QTimer()
        self.update_timer_2 = QtCore.QTimer()
        self.update_timer_3 = QtCore.QTimer()
        self.update_timer_4 = QtCore.QTimer()
        self.update_timer_5 = QtCore.QTimer()
        self.update_timer_1.start(2000)
        self.update_timer_2.start(8000)
        self.update_timer_3.start(10000)
        self.update_timer_4.start(15000)
        self.update_timer_5.start(20000)
        self.init_slot()

        try:
            geoip_db = os.getenv("GEOLITE2_DB_PATH", "GeoLite2-City.mmdb")
            self.geoip_reader = geoip2.database.Reader(geoip_db)
            print(f"GeoLite2 数据库加载成功: {geoip_db}")
        except Exception as e:
            print(f"GeoLite2 数据库加载失败: {e}")

        self.save_button.clicked.connect(self.save_all_records)

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_auth_log)
        self.monitor_thread.start()

    def init_slot(self):

        self.update_timer_1.timeout.connect(self.Data_Acquisition)
        self.update_timer_2.timeout.connect(self.Data_ip)
        self.update_timer_3.timeout.connect(self.Unauthorized)
        self.update_timer_4.timeout.connect(self.Read_Btmp_Log)
        self.update_timer_5.timeout.connect(self.Read_Auth_Log)
        self.connect_linux()

    def connect_linux(self):

        try:
            self.btmp_log_path = '/var/log/btmp'
            self.auth_log_path = '/var/log/auth.log'
            self.hostname = ''
            self.username = ''
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(self.hostname, 22, username=self.username, password=self.username)
            print("Connected to the server.")
        except Exception as e:
            print(f"Failed to connect to the server: {e}")

    def Data_Acquisition(self):

        try:
            stdin, stdout, stderr = self.client.exec_command('top -b -n 1')
            self.output = stdout.read().decode('utf-8', errors='ignore')

            self.cpu_idle_percentage = re.search(r',\s*([\d.]+)\sid,', self.output)
            if self.cpu_idle_percentage:
                idle_percentage = self.cpu_idle_percentage.group(1)
                print("CPU利用率:", round(100 - float(idle_percentage), 2))
                cpu = "CPU利用率： {:.2f}%".format(100 - float(idle_percentage))
                self.label.setText(cpu)
            else:
                print("未找到CPU利用率")

            rows = self.output.splitlines()
            result = [row.split() for row in rows]

            task = "总任务数：" + result[1][1]
            self.label_2.setText(task)

            mem = round(float(result[3][5]) / float(result[3][3]) * 100, 2)
            mem = "内存占用率：" + str(mem) + '%'
            self.label_3.setText(mem)

            data = result[7:]
            for row in data:
                row.pop(7)

            self.tableWidget.setRowCount(0)
            for i in range(len(data)):
                self.tableWidget.insertRow(i)
                for j in range(len(data[i])):
                    self.tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(str(data[i][j])))

        except Exception as e:
            print(f"Error in Data_Acquisition: {e}")

    def Data_ip(self):

        try:
            stdin, stdout, stderr = self.client.exec_command('who')
            self.out = stdout.read().decode('utf-8', errors='ignore')

            rows = self.out.split()
            print(rows)

            result = [rows]
            print('result:', result)

            data_list = result
            self.tableWidget_2.setRowCount(0)
            self.tableWidget_2.setColumnCount(len(data_list[0]))

            for i in range(len(data_list)):
                self.tableWidget_2.insertRow(i)
                for j in range(len(data_list[i])):
                    print(i, j, data_list[i][j])
                    if data_list[i][j] == '(:0)':
                        data_list[i][j] = '192.168.116.140'
                    item = QtWidgets.QTableWidgetItem(str(data_list[i][j]))
                    self.tableWidget_2.setItem(i, j, item)

        except Exception as e:
            print(f"Error in Data_ip: {e}")

    def Unauthorized(self):

        try:
            stdin, stdout, stderr = self.client.exec_command("cat /var/log/auth.log | strings | grep sudo")
            self.out_1 = stdout.read().decode('utf-8', errors='ignore')
            self.err_1 = stderr.read().decode('utf-8', errors='ignore')

            print("stdout:", self.out_1)
            print("stderr:", self.err_1)

            if self.out_1.strip():
                rows = self.out_1.split('\n')
                print(rows)
                self.tableWidget_3.setRowCount(0)
                for i in range(len(rows)):
                    self.tableWidget_3.insertRow(i)
                    item = QtWidgets.QTableWidgetItem(str(rows[i]))
                    self.tableWidget_3.setItem(i, 0, item)
            else:
                print("No output from sudo filter command")

            if self.err_1.strip():
                print("Error executing sudo filter command:", self.err_1)

        except Exception as e:
            print(f"Error in Unauthorized: {e}")

    def Read_Btmp_Log(self):

        try:
            stdin, stdout, stderr = self.client.exec_command('lastb')
            lastb_output = stdout.read().decode('utf-8', errors='ignore')
            print("lastb output:", lastb_output[:1000])

            lastb_lines = lastb_output.split('\n')
            print("Number of lines in lastb output:", len(lastb_lines))

            logins = []
            for line in lastb_lines:
                parts = line.split()
                if len(parts) < 10:
                    continue

                user = parts[0]
                tty = parts[1]
                ip = parts[2]
                date_match = re.search(r'\b\w{3}\s+\w{3}\s+\d+\s+\d+:\d+', line)
                date = date_match.group(0) if date_match else "Unknown"
                location = "Unknown"
                if re.match(r'(\d{1,3}\.){3}\d{1,3}', ip):
                    try:
                        response = self.geoip_reader.city(ip)
                        location = f"{response.country.name} {response.city.name}"
                    except Exception as e:
                        print(f"GeoIP lookup failed for {ip}: {e}")
                logins.append((user, tty, ip, date, location))

            logins = sorted(logins, key=lambda x: time.strptime(x[3], '%a %b %d %H:%M'), reverse=True)[:10]
            print("Parsed btmp data:", logins)

            self.tableWidget_5.setRowCount(0)
            for i, data in enumerate(logins):
                self.tableWidget_5.insertRow(i)
                self.tableWidget_5.setItem(i, 0, QtWidgets.QTableWidgetItem(data[0]))
                self.tableWidget_5.setItem(i, 1, QtWidgets.QTableWidgetItem(data[1]))
                self.tableWidget_5.setItem(i, 2, QtWidgets.QTableWidgetItem(data[2]))
                self.tableWidget_5.setItem(i, 3, QtWidgets.QTableWidgetItem(data[3]))
                self.tableWidget_5.setItem(i, 4, QtWidgets.QTableWidgetItem(data[4]))

        except Exception as e:
            print(f"Error reading btmp: {e}")

    def Read_Auth_Log(self):

        try:
            stdin, stdout, stderr = self.client.exec_command(f'cat {self.auth_log_path}')
            auth_log_output = stdout.read().decode('utf-8', errors='ignore')
            print("auth.log output:", auth_log_output[:1000])

            auth_log_lines = auth_log_output.split('\n')
            print("Number of lines in auth.log output:", len(auth_log_lines))

            logins = []
            for line in auth_log_lines:
                if "Failed password" in line or "Accepted password" in line or "session opened" in line:
                    parts = line.split()
                    date = " ".join(parts[0:3])
                    user = "root"
                    event_start_index = line.find(parts[4])
                    event = line[event_start_index:]
                    ip = parts[-4] if "Failed password" in line or "Accepted password" in line else "N/A"
                    location = "Unknown"
                    if re.match(r'(\d{1,3}\.){3}\d{1,3}', ip):
                        try:
                            response = self.geoip_reader.city(ip)
                            location = f"{response.country.name} {response.city.name}"
                        except Exception as e:
                            print(f"GeoIP lookup failed for {ip}: {e}")
                    logins.append((date, user, event, ip, location))

            print("Parsed auth.log data:", logins)

            self.tableWidget_6.setRowCount(0)
            for i, data in enumerate(logins):
                self.tableWidget_6.insertRow(i)
                self.tableWidget_6.setItem(i, 0, QtWidgets.QTableWidgetItem(data[0]))
                self.tableWidget_6.setItem(i, 1, QtWidgets.QTableWidgetItem(data[1]))
                self.tableWidget_6.setItem(i, 2, QtWidgets.QTableWidgetItem(data[2]))
                self.tableWidget_6.setItem(i, 3, QtWidgets.QTableWidgetItem(data[3]))
                self.tableWidget_6.setItem(i, 4, QtWidgets.QTableWidgetItem(data[4]))

        except Exception as e:
            print(f"Error reading auth.log: {e}")

    def monitor_auth_log(self):

        previous_size = 0
        while self.monitoring:
            try:

                stdin, stdout, stderr = self.client.exec_command(f'stat -c %s {self.auth_log_path}')
                current_size = int(stdout.read().strip())
                if current_size > previous_size:

                    stdin, stdout, stderr = self.client.exec_command(
                        f'tail -c +{previous_size + 1} {self.auth_log_path}')
                    new_logs = stdout.read().decode('utf-8', errors='ignore')
                    self.check_for_alerts(new_logs)
                    previous_size = current_size
                time.sleep(5)
            except Exception as e:
                print(f"Error monitoring auth.log: {e}")

    def check_for_alerts(self, logs):

        for line in logs.split('\n'):
            if "Failed password" in line or "Accepted password" in line:
                self.alert_log.append(f"ALERT: {line}")
                print(f"ALERT: {line}")

    def save_all_records(self):
        save_path = os.path.join(os.path.dirname(__file__), "log")
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, "log.txt")

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write("CPU 利用率: {}\n".format(self.label.text()))
            file.write("内存使用占比: {}\n".format(self.label_3.text()))
            file.write("任务总数: {}\n\n".format(self.label_2.text()))

            file.write("登录记录:\n")
            self.save_table_to_txt(file, self.tableWidget_2)

            file.write("\n异常示例:\n")
            self.save_table_to_txt(file, self.tableWidget_3)

            file.write("\n异常登陆状况:\n")
            self.save_table_to_txt(file, self.tableWidget_5)

            file.write("\nauth.log 记录:\n")
            self.save_table_to_txt(file, self.tableWidget_6)

        print(f"记录已保存到 {file_path}")

    def save_table_to_txt(self, file, table):
        row_count = table.rowCount()
        column_count = table.columnCount()

        for row in range(row_count):
            row_data = []
            for column in range(column_count):
                item = table.item(row, column)
                row_data.append(item.text() if item is not None else "")
            file.write("\t".join(row_data) + "\n")
