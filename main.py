import paramiko

hostname = '' # IP地址
username = '' # 用户名

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

client.connect(hostname, username=username)

stdin, stdout, stderr = client.exec_command("cat /var/log/auth.log | strings | grep sudo")

output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8')

print('输出：', output)
print('错误：', error)

client.close()
