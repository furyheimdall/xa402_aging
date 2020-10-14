#!/bin/bash

#default configuration
bot_token=""
title="Unnamed Aging"
ip="192.168.2.166"
time=`date "+%Y%m%d%H%M"`;
memory_fetching_interval=10     #sec
memory_monitoring_package="com.humaxdigital.corona.tvinput.jcom"
#memory_monitoring_package="com.humaxdigital.alps.demo.player"
#memory_monitoring_package="com.google.android.exoplayer2.demo"

adb=
prefix=
logcat_module_pid=
memory_monitor_pid=

update_config() {
    adb="adb -s ${ip}:5555"
    prefix="${adb} shell"    
}

# execute secnario
do_exec() {
    #scenario
    #scenario_nothingtodo
    #scenario_exo_leak
    #scenario_test
    #scenario_rec_play
    #scenario_rec_play2
    scenario_sqe_scenario
}

do_precondition() {
    echo "Enable corona deadlock debugger"
    ${prefix} setprop persist.vendor.humax.corona.deadlock true
    echo "Enable Alps debug log"
    ${prefix} setprop persist.alps.system.debug.log true
}

###################################################################################################


scenario_nothingtodo() {
    echo "aging on progress..."
    sleep 10;
}

scenario_test() {
    ${prefix} input keyevent KEYCODE_ENTER
    sleep 210;
    ${prefix} input keyevent KEYCODE_BACK
    sleep 30;
}

scenario_exo_leak() {
    ${prefix} am start -a com.google.android.exoplayer.demo.action.VIEW -d "file:///storage/emulated/0/testvid.ts"
    sleep 210;
    ${prefix} input keyevent KEYCODE_BACK
    sleep 15;
}

scenario() {
    echo "channel change to DT 11"
    ${prefix} input keyevent KEYCODE_0 KEYCODE_1 KEYCODE_1;
    sleep 10;

    echo "channel change to BS 101"
    ${prefix} input keyevent KEYCODE_1 KEYCODE_0 KEYCODE_1;
    sleep 2;

    echo "channel change to BS 101"
    sleep 10;

    echo "channel change to BS4K 101"
    ${prefix} input keyevent KEYCODE_1 KEYCODE_0 KEYCODE_1;
    sleep 2;
    ${prefix} input keyevent KEYCODE_DPAD_DOWN KEYCODE_DPAD_DOWN KEYCODE_OK
    sleep 10;

    echo "channel change to CATV 604"
    ${prefix} input keyevent KEYCODE_6 KEYCODE_0 KEYCODE_4;
    sleep 10;
}


scenario_rec_play() {
    ${prefix} input keyevent 201
    sleep 2;
    ${prefix} input keyevent KEYCODE_ENTER
    sleep 1;
    ${prefix} input keyevent KEYCODE_DPAD_RIGHT
    sleep 1;
    ${prefix} input keyevent KEYCODE_ENTER
    sleep 5;
    ${prefix} input keyevent HOME
    sleep 8;
}

scenario_rec_play2() {
    ${prefix} input keyevent KEYCODE_DPAD_CENTER 
    sleep 1
    ${prefix} input keyevent KEYCODE_DPAD_RIGHT
    sleep 1
    echo "REC Play Start"
    ${prefix} input keyevent KEYCODE_DPAD_CENTER
    sleep 3
    echo "REC Play Stop"
    ${prefix} input keyevent KEYCODE_BACK
    sleep 1
}

scenario_sqe_scenario() {
    ${prefix} input keyevent KEYCODE_0 && ${prefix} input keyevent KEYCODE_1 && ${prefix} input keyevent KEYCODE_1
    sleep 5
    
    ${prefix} input keyevent KEYCODE_2
    sleep 10
    ${prefix} input keyevent CHANNEL_UP
    sleep 10
    ${prefix} input keyevent CHANNEL_UP
    sleep 5
    ${prefix} input keyevent CHANNEL_DOWN
    sleep 10
    ${prefix} input keyevent 198
    sleep 5
    ${prefix} input keyevent KEYCODE_DPAD_CENTER
    sleep 5
    ${prefix} input keyevent 172
    sleep 10
    ${prefix} input keyevent 193
    sleep 10
    ${prefix} input keyevent 130
    sleep 300
    ${prefix} input keyevent 86
    sleep 2
    ${prefix} input keyevent KEYCODE_DPAD_CENTER
    sleep 10
    ${prefix} input keyevent CHANNEL_UP
    sleep 15
    ${prefix} input keyevent 175
    sleep 15
    ${prefix} input keyevent KEYCODE_4
    sleep 20
    ${prefix} input keyevent 230
    sleep 10
    ${prefix} input keyevent 189
    sleep 5
    ${prefix} input keyevent 172
    sleep 5
    ${prefix} input keyevent KEYCODE_DPAD_CENTER
    sleep 5
    ${prefix} input keyevent KEYCODE_DPAD_CENTER
    sleep 5
    ${prefix} input keyevent 201
    sleep 5
    ${prefix} input keyevent KEYCODE_DPAD_CENTER
    sleep 10
    ${prefix} input keyevent 192
    sleep 10
    ${prefix} input keyevent KEYCODE_3
    sleep 2
    ${prefix} input keyevent KEYCODE_0
    sleep 2
    ${prefix} input keyevent KEYCODE_2
    sleep 10
    ${prefix} input keyevent 222
    sleep 10
    ${prefix} input keyevent 222
    sleep 10
    ${prefix} input keyevent 194
    sleep 10
    ${prefix} input keyevent KEYCODE_1
    sleep 10
    ${prefix} input keyevent 190
    sleep 10
    ${prefix} input keyevent 191
    sleep 60
    ${prefix} input keyevent BACK
    sleep 10
    ${prefix} input keyevent BACK
    sleep 10
    ${prefix} input keyevent 193
    sleep 10
    ${prefix} input keyevent KEYCODE_1
    sleep 10
    ${prefix} input keyevent KEYCODE_2
    sleep 2
    ${prefix} input keyevent KEYCODE_0
    sleep 2
    ${prefix} input keyevent KEYCODE_0
    sleep 6
    ${prefix} input keyevent KEYCODE_1
    sleep 1144
}

fetching_memory() {
    echo "* starting memory monitor... >> ${memory_monitoring_package}"
    echo "Aging Name : ${title}" >> ${mem_target}
    echo "Target device IP : ${ip}" >> ${mem_target}
    echo "Running on : $(echo $(whoami)@$(hostname)[$(hostname -I))]" >> ${mem_target}
    echo "Aging Path : $(pwd)" >> ${mem_target}
    echo "S/W fingerprint : ${fingerprint}" >> ${mem_target}
    echo "memory monitoring on package ${memory_monitoring_package}" >> ${mem_target}
    echo "" >> ${mem_target}
    monitoring_pid="0"
    while [ 1 ]
    do
        check_pid=$(${prefix} pidof ${memory_monitoring_package})
        system_server_pid=$(${prefix} pidof system_server)
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        echo "Current Time : ${timestamp}" >> ${mem_target}
        if [ ${monitoring_pid} != ${check_pid} ];then
          echo "* PID of package [${memory_monitoring_package}] has been changed : ${monitoring_pid} =>  ${check_pid} "
          echo "* PID of package [${memory_monitoring_package}] has been changed : ${monitoring_pid} =>  ${check_pid} " >> ${mem_target}
          monitoring_pid=${check_pid}
        fi
        ${prefix} dumpsys meminfo ${memory_monitoring_package} | grep "Java Heap:" >> ${mem_target}
        ${prefix} dumpsys meminfo ${memory_monitoring_package} | grep "Native Heap:" >> ${mem_target}
        ${prefix} cat /sys/kernel/debug/binder/proc/${check_pid} | grep node | wc -l | xargs echo "         Binder total : " >> ${mem_target}
        ${prefix} cat /sys/kernel/debug/binder/proc/${check_pid} | grep ${system_server_pid} | wc -l | xargs echo "         Binder related to system server : " >> ${mem_target}
        logd_mem=$(${prefix} dumpsys meminfo logd | grep "Native Heap:" | cut -c 25-)
        bmem=$(${prefix} cat /proc/brcm/core | grep "MAIN" | cut -f 2 -d '%' | tr -d ' ')
        logservice_cpu=$(${prefix} top -b -n 1 | grep com.humaxdigital.atv.logservice | sed '/grep/d' | awk '{ print $9}')
        echo "Logd NatvHeap:${logd_mem}" >> ${mem_target}
        echo "Bmem Peak:${bmem}" >> ${mem_target}
        echo "LogService CPU:${logservice_cpu}" >> ${mem_target}
        echo "" >> ${mem_target}
        sleep ${memory_fetching_interval};
    done
}

print_usage() {
    echo "Usage:"
    echo "./aging.sh [-b BOT_TOKEN] [-i IP] [-t AGING_TITLE] [-m MONITORING_PACKAGE] [-s MONITORING_INTERVAL]"
    echo "    if there is no option, script will use default value"
    echo "    Deafult Bot : ${bot_token}"
    echo "    Default IP : ${ip}"
    echo "    Default Title : ${title}"
    echo "    Default Package : ${memory_monitoring_package}"
    echo "    Default Interval in sec : ${memory_fetching_interval}"
}

while (( "$#" )); do
    case "$1" in
        -h|--help)
            print_usage
            exit 0
            ;;
        -b|--bot)
            bot_token=$2
            shift 2
            ;;
        -t|--title)
            title=$2
            shift 2
            ;;
        -i|--ip)
            ip=$2
            shift 2
            ;;
        -m|--monitoring)
            memory_monitoring_package=$2
            shift 2
            ;;
        -s|--sec)
            memory_fetching_interval=$2
            shift 2
            ;;
        *)
            echo "Unsupported option $1" >&2
            print_usage
            exit 1
            ;;
    esac
done

update_config

echo "* disconnect adb..."
adb disconnect ${ip}
sleep 2
echo "* starting adb..."
adb connect ${ip}
sleep 1 && ${adb} root
# again
sleep 1 && adb connect ${ip}
sleep 1 && ${adb} root
echo "* Fetching Device info..."
model=$(${prefix} getprop ro.product.model)
fingerprint=$(${prefix} getprop ro.build.fingerprint)
echo "MODEL : ${model}"
echo "FINGER PRINT : ${fingerprint}"
logcat_target="${time}_${model}_logcat.txt"
mem_target="${time}_${model}_memlog.txt"
rm -rf ${mem_target}
touch ${mem_target}
do_precondition
echo "* starting logcat..."
${prefix} logcat -c
${prefix} logcat > ${logcat_target} &
logcat_module_pid=$! 
fetching_memory & 
memory_monitor_pid=$!

if [ ! -z ${bot_token} ]; then
    python3 reportbot.py ${bot_token} ${mem_target} ${logcat_target} &
    bot_pid=$!
else
    echo "* Bot token was not given. Start aging without bot"
fi

sleep 2;

echo "* LOGCAT monitor PID = ${logcat_module_pid}"
echo "* Memory monitor PID = ${memory_monitor_pid}"
echo "* Start to reporting bot = ${bot_pid}"
echo "* Aging Started >>> ${title} <<< "
trap "kill ${logcat_module_pid} ${memory_monitor_pid} ${bot_pid}; echo 'related process will be cleaned up';exit 0" INT TERM QUIT

count=0
while [ 1 ]
do
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    count=$(($count+1))
    echo "[${timestamp}] Execution Aging Scenario : Count ($count)"
    do_exec
done
