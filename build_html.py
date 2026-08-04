# -*- coding: utf-8 -*-
"""
多国考勤HTML日历生成器 v4 (多月份切换)
支持通过 —input 传入多个月份JSON数据，在HTML中通过下拉框切换月份。

用法:
  python build_html.py —input june.json —input july.json —output calendar.html
  python build_html.py —config config.json                        # 单月(向后兼容)
"""

import json
import os
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')


def build_html(data_sources, output_path=None):
    """从多个月份JSON数据生成支持月份切换的HTML日历
    
    data_sources: list of (json_path, label) tuples
    """
    all_months_data = {}
    month_labels = {}
    month_keys_ordered = []
    total_days = 30  # fallback

    for json_path, label in data_sources:
        with open(json_path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        yr = d.get('year', 2026)
        mo = d.get('month', 6)
        mkey = f"{yr}-{mo:02d}"
        all_months_data[mkey] = d
        month_labels[mkey] = label or f"{yr}年{mo}月"
        month_keys_ordered.append(mkey)
        total_days = max(total_days, d.get('month_days', 30))

    # Default to first month
    default_mkey = month_keys_ordered[0]
    default_data = all_months_data[default_mkey]
    country_name = default_data.get('country_name', '多国')

    html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>考勤日历（月度切换）</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333;min-height:100vh}
.header{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.header h1{font-size:20px;font-weight:600}
.header .subtitle{font-size:12px;opacity:.7;margin-left:8px}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.controls select,.controls input{padding:8px 12px;border-radius:6px;border:none;font-size:14px;min-width:200px;background:#fff;color:#333}
.controls .month-select{background:rgba(255,255,255,.15);color:#fff;min-width:120px}
.controls .month-select option{background:#fff;color:#333}
.controls .search-box{background:rgba(255,255,255,.2);color:#fff;width:200px}
.controls .search-box::placeholder{color:rgba(255,255,255,.6)}
.info-tag{display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;margin-left:6px}
.info-tag.blue-collar{background:#ff9800;color:#fff}
.info-tag.white-collar{background:#2196f3;color:#fff}
.info-tag.warn{background:#ff5252;color:#fff}
.info-tag.info{background:#4caf50;color:#fff}
.main{max-width:1300px;margin:0 auto;padding:20px}
.alert-bar{background:#fff3e0;border:1px solid #ff9800;border-radius:8px;padding:10px 16px;margin-bottom:12px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;font-size:13px;display:none}
.alert-bar.show{display:flex}
.alert-item{display:flex;align-items:center;gap:4px}
.alert-item.warn{color:#e65100;font-weight:600}
.alert-item.info{color:#1565c0}
.emp-bar{background:#fff;border-radius:10px;padding:16px 20px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;display:none}
.emp-bar .name{font-size:18px;font-weight:700}
.emp-bar .stats{display:flex;gap:20px;font-size:14px}
.emp-bar .stats span{color:#666}
.emp-bar .stats strong{color:#1a237e}
.legend{background:#fff;border-radius:10px;padding:10px 20px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);display:flex;gap:18px;flex-wrap:wrap;font-size:12px;align-items:center}
.legend-item{display:flex;align-items:center;gap:6px}
.legend-dot{width:12px;height:12px;border-radius:3px}
.calendar{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden}
.cal-header{display:grid;grid-template-columns:repeat(7,1fr);text-align:center;background:#1a237e}
.cal-header .wh{padding:8px 4px;color:rgba(255,255,255,.7);font-size:12px}
.cal-header .wh.we{color:#ff8a80}
.cal-week{display:grid;grid-template-columns:repeat(7,1fr)}
.cal-cell{border:2px solid #e8eaf6;padding:5px 4px;display:flex;flex-direction:column;min-height:105px;font-size:12px;position:relative;background:#fff}
.cal-cell:hover{background:#f5f5ff}
.cal-cell.weekend{background:#fafafa;border-color:#eee}
.cal-cell.no-data{background:#f9f9f9;color:#ccc}
.cal-cell.leave{background:#e3f2fd;border-color:#90caf9}
.cal-cell.off{background:#f3e5f5;border-color:#ce93d8}
.cal-cell.has-ot{background:#fff8e1}
.cal-cell.has-ot100{background:#ffebee}
.cal-cell.unknown{background:#fff3e0;border-color:#ffcc80}
.cal-cell.partial-day{border:2px solid #ff9800;background:#fffde7}
.cal-cell.missing-punch{border:2px dashed #f44336;background:#fff5f5}
.cal-cell.both-warn{border:2px solid #ff6d00;background:#fff8e1}
.cal-cell .day-num{font-size:11px;color:#999;margin-bottom:1px;font-weight:500}
.cal-cell.weekend .day-num{color:#c62828}
.cal-cell .wd{font-size:10px;color:#bbb;margin-left:3px}
.cal-cell .data-block{flex:1;display:flex;flex-direction:column;justify-content:center;gap:1px}
.cal-cell .total-h{font-size:15px;font-weight:700;color:#1a237e}
.cal-cell .breakdown{font-size:11px;line-height:1.5}
.cal-cell .br-w{color:#2e7d32;font-weight:500}
.cal-cell .br-e{color:#e65100;font-weight:500}
.cal-cell .br-o{color:#c62828;font-weight:600}
.cal-cell .br-toil{color:#7b1fa2;font-weight:500}
.cal-cell .leave-tag{display:inline-block;font-size:11px;font-weight:700;padding:2px 6px;border-radius:3px;background:#bbdefb;color:#1565c0}
.cal-cell .leave-name{font-size:10px;color:#546e7a;margin-top:1px}
.cal-cell .source-badge{position:absolute;top:3px;right:4px;font-size:9px;padding:1px 4px;border-radius:3px}
.cal-cell .source-badge.sys{background:#e8f5e9;color:#2e7d32}
.cal-cell .source-badge.man{background:#fff3e0;color:#e65100}
.cal-cell .source-badge.miss{background:#ffebee;color:#c62828;font-weight:600}
.cal-cell .warn-tag{position:absolute;bottom:3px;left:4px;font-size:9px;font-weight:700;padding:1px 4px;border-radius:3px}
.cal-cell .warn-tag.partial{background:#fff3e0;color:#e65100}
.cal-cell .warn-tag.miss-punch{background:#ffebee;color:#c62828}
.cal-cell .comment-hint{font-size:9px;color:#9e9e9e;font-style:italic;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:120px}
.monthly-summary{background:#1a237e;color:#fff;padding:12px 20px;display:flex;gap:16px;font-size:13px;align-items:center;flex-wrap:wrap}
.ms-group{display:flex;gap:16px;margin-left:auto}
.ms-item{display:flex;flex-direction:column;align-items:center;min-width:50px}
.ms-label{font-size:9px;opacity:.7}
.ms-value{font-size:18px;font-weight:700}
.ms-value.ot{color:#ff8a80}
.ms-value.extra{color:#ffcc80}
.ms-value.worked{color:#a5d6a7}
.notes{background:#fff;border-radius:10px;padding:16px 20px;margin-top:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);display:none}
.notes.show{display:block}
.notes h3{font-size:14px;margin-bottom:10px;color:#1a237e}
.note-item{font-size:12px;padding:3px 0;border-bottom:1px solid #f0f0f0}
.note-item.warn{color:#e65100}
.note-item.alert{color:#c62828;font-weight:600}
.note-item.info{color:#666}
@media(max-width:768px){.cal-cell{min-height:80px;font-size:10px}.cal-cell .total-h{font-size:12px}.controls{flex-wrap:wrap}.controls select,.controls input{min-width:140px}}
</style></head><body>
<div class="header"><h1><span id="countryTitle">多国</span> 考勤日历 <span class="subtitle">月度切换</span></h1><div class="controls"><select class="month-select" id="monthSelect"></select><input type="text" class="search-box" id="searchBox" placeholder="搜索姓名..."><select id="empSelect"><option value="">-- 选择员工 --</option></select></div></div>
<div class="main">
<div class="alert-bar" id="alertBar"></div>
<div class="emp-bar" id="empBar"><div><span class="name" id="empName"></span><span class="info-tag" id="empType"></span><span class="info-tag warn" id="empNoData1" style="display:none">无系统打卡</span><span class="info-tag info" id="empHasData1" style="display:none">有系统打卡</span><span style="font-size:12px;color:#999;margin-left:8px" id="empD1Name"></span></div><div class="stats" id="monthlyStats"></div></div>
<div class="legend"><span style="font-weight:600;color:#1a237e">图例:</span>
<div class="legend-item"><div class="legend-dot" style="background:#fff;border:1px solid #ddd"></div>正常</div>
<div class="legend-item"><div class="legend-dot" style="background:#fff8e1"></div>有调休</div>
<div class="legend-item"><div class="legend-dot" style="background:#ffebee"></div>有加班费</div>
<div class="legend-item"><div class="legend-dot" style="background:#e3f2fd"></div>请假</div>
<div class="legend-item"><div class="legend-dot" style="background:#f3e5f5"></div>休息(OFF)</div>
<div class="legend-item"><div class="legend-dot" style="background:#fafafa;border:2px solid #eee"></div>周末</div>
<div class="legend-item"><div class="legend-dot" style="background:#fffde7;border:2px solid #ff9800"></div>不满勤</div>
<div class="legend-item"><div class="legend-dot" style="background:#fff5f5;border:2px dashed #f44336"></div>异常缺卡</div>
<div class="legend-item"><div class="legend-dot" style="background:#fff3e0;border:2px solid #ffcc80"></div>待确认</div>
</div>
<div class="calendar" id="calendar">
<div class="cal-header"><div class="wh">周一</div><div class="wh">周二</div><div class="wh">周三</div><div class="wh">周四</div><div class="wh">周五</div><div class="wh we">周六</div><div class="wh we">周日</div></div>
<div id="calBody"></div><div id="monthlyBar" class="monthly-summary"></div>
</div>
<div class="notes" id="notes"><h3>注意事项 &amp; 待确认项</h3><div id="notesContent"></div></div>
</div>
<script>
__DATA_JSON__
</script></body></html>'''

    # Build JS — embed all months as a dictionary keyed by "YYYY-MM"
    months_js = {}
    for mkey, d in all_months_data.items():
        months_js[mkey] = d

    jso = json.dumps(months_js, ensure_ascii=False)

    js = r'''var ALL_MONTHS=__JSON__;
var MONTH_KEYS=__MONTH_KEYS__;
var MONTH_LABELS=__MONTH_LABELS__;
var DEFAULT_MKEY="__DEFAULT_MKEY__";
var COUNTRY_NAME="__COUNTRY_NAME__";
var WD_CN=['一','二','三','四','五','六','日'];
var currentMKey=DEFAULT_MKEY;
var currentEmpIdx=-1;

function getCD(){return ALL_MONTHS[currentMKey]}
function getMD(){return getCD().month_days}

function buildMonthSelect(){
 var ms=document.getElementById('monthSelect');
 MONTH_KEYS.forEach(function(k){
  var o=document.createElement('option');o.value=k;o.textContent=MONTH_LABELS[k];ms.appendChild(o)
 });
 ms.value=DEFAULT_MKEY;
 ms.addEventListener('change',function(){
  currentMKey=ms.value;
  rebuildEmpList();
  var si=document.getElementById('empSelect');
  if(currentEmpIdx>=0){
   // Try to find the same employee in the new month by name
   var targetName=null;
   try{targetName=getCD().employees[currentEmpIdx].name}catch(e){}
   if(targetName){
    var found=-1;
    getCD().employees.forEach(function(e,i){if(e.name===targetName)found=i});
    if(found>=0){si.value=found;currentEmpIdx=found;render(getCD().employees[found]);return}
   }
  }
  // Fallback: select first employee
  if(getCD().employees.length>0){si.value='0';currentEmpIdx=0;render(getCD().employees[0])}else{clear()}
 })
}

function rebuildEmpList(){
 var s=document.getElementById('empSelect');
 s.innerHTML='<option value="">-- 选择员工 --</option>';
 var data=getCD();
 data.employees.forEach(function(e,i){
  var o=document.createElement('option');o.value=i;o.textContent=e.name+' ['+e.type+']';s.appendChild(o)
 });
 s.addEventListener('change',function(){
  document.getElementById('searchBox').value='';
  var i=s.value;
  if(i!==''){currentEmpIdx=parseInt(i);render(data.employees[parseInt(i)])}else{currentEmpIdx=-1;clear()}
 });
}

function init(){
 document.getElementById('countryTitle').textContent=COUNTRY_NAME;
 document.title=COUNTRY_NAME+' 考勤日历（月度切换）';

 buildMonthSelect();
 var s=document.getElementById('empSelect'),b=document.getElementById('searchBox');
 rebuildEmpList();
 // Re-attach search handler
 b.addEventListener('input',function(){
  var q=b.value.toLowerCase().trim();s.value='';
  if(!q){clear();return}
  var data=getCD();
  var m=data.employees.find(function(e){return e.name.toLowerCase().includes(q)});
  if(m){var idx=data.employees.indexOf(m);s.value=idx;currentEmpIdx=idx;render(m)}else{clear()}
 });
 if(getCD().employees.length>0){s.value='0';currentEmpIdx=0;render(getCD().employees[0])}
}

function clear(){
 document.getElementById('empBar').style.display='none';
 document.getElementById('alertBar').classList.remove('show');
 document.getElementById('calBody').innerHTML='';
 document.getElementById('monthlyBar').innerHTML='';
 document.getElementById('notes').classList.remove('show')
}

function render(emp){
 var d1n=emp.d1_name||'',d2n=emp.name;
 document.getElementById('empName').textContent=d1n&&d1n!=d2n?d1n+'（排班: '+d2n+'）':d2n;
 var t=document.getElementById('empType');t.textContent=emp.type;t.className='info-tag '+(emp.is_blue_collar?'blue-collar':'white-collar');
 document.getElementById('empD1Name').textContent='';
 document.getElementById('empNoData1').style.display=emp.has_any_data1?'none':'inline-block';
 document.getElementById('empHasData1').style.display=emp.has_any_data1?'inline-block':'none';
 document.getElementById('empBar').style.display='flex';
 var ms=emp.monthly_summary;
 document.getElementById('monthlyStats').innerHTML='<span>总实际 <strong>'+ms.total_actual+'h</strong></span><span>正常 <strong style="color:#2e7d32">'+ms.total_worked+'h</strong></span><span>调休 <strong style="color:#e65100">'+ms.total_extra+'h</strong></span><span>加班费 <strong style="color:#c62828">'+ms.total_ot100+'h</strong></span>';
 var alerts=emp.alerts||[],ab=document.getElementById('alertBar');
 if(alerts.length>0){ab.classList.add('show');ab.innerHTML='<span style="font-weight:600;margin-right:4px">WARNING</span>'+alerts.map(function(a){return'<span class="alert-item '+(a.indexOf('不满勤')>=0?'warn':'info')+'">'+a+'</span>'}).join('')}else{ab.classList.remove('show')}
 renderCalendar(emp);renderNotes(emp)
}

function renderCalendar(emp){
 var body=document.getElementById('calBody');body.innerHTML='';
 var data=getCD();
 var yr=data.year,mo=data.month,md=getMD();
 var startOffset=(new Date(yr,mo-1,1).getDay()+6)%7;
 var weeks=Math.ceil((md+startOffset)/7);
 var pDays=emp.prev_month_days||[];
 for(var w=0;w<weeks;w++){
  var row=document.createElement('div');row.className='cal-week';
  for(var c=0;c<7;c++){
   var day=w*7+c+1-startOffset,cell=document.createElement('div');cell.className='cal-cell';
   if(day<1||day>md){
    if(day<1&&w===0){
     var pmDay=29+c;
     var pd=pDays.find(function(d){return d.prev_month_day===pmDay});
     if(pd){
      cell.classList.add('no-data');
      cell.style.border='1px dashed #bdbdbd';
      cell.style.background='#f5f5f5';
      var pmInfo='<span class="day-num" style="font-size:10px;color:#9e9e9e">'+yr+'/'+(mo-1)+'/'+pmDay+'<span class="wd" style="font-size:9px;color:#bbb">'+WD_CN[(new Date(yr,mo-2,pmDay).getDay()+6)%7]+'</span></span>';
      if(pd.status==='leave'){if(pd.leave_code==='OFF')cell.classList.add('off');else cell.classList.add('leave');
       cell.classList.add('leave');
       pmInfo+='<div class="data-block"><div class="leave-tag" style="font-size:10px">'+(pd.leave_code||'REST')+'</div><div class="leave-name" style="font-size:9px">'+(pd.leave_name||'')+'</div></div>'
      }else if(pd.actual_hours>0){
       pmInfo+='<div class="data-block"><div class="total-h" style="font-size:13px;color:#757575">'+pd.actual_hours.toFixed(2)+'h</div><div class="breakdown" style="font-size:10px;color:#9e9e9e"><span class="br-w">'+pd.worked.toFixed(2)+' worked</span></div></div>'
      }
      cell.innerHTML=pmInfo;
     }else{cell.classList.add('no-data');cell.innerHTML='<span class="day-num">&nbsp;</span>'}
    }else{cell.classList.add('no-data');cell.innerHTML='<span class="day-num">&nbsp;</span>'}
   }
   else{
    var info=emp.days[String(day)],wkday=(new Date(yr,mo-1,day).getDay()+6)%7,isWE=wkday>=5;
    cell.innerHTML='<span class="day-num">'+day+'<span class="wd">'+WD_CN[wkday]+'</span></span>';
    if(info.status==='leave'){if(info.leave_code==='OFF')cell.classList.add('off');else cell.classList.add('leave');
     cell.classList.add('leave');
     cell.innerHTML+='<div class="data-block"><div class="leave-tag">'+(info.leave_code||'REST')+'</div><div class="leave-name">'+(info.leave_name||'')+'</div></div>'
    }else if(info.status==='unknown_note'){
     cell.classList.add('unknown');
     cell.innerHTML+='<div class="data-block"><div class="br-o">待确认</div><div class="leave-name">'+(info.note_raw||'')+'</div></div>'
    }else if(info.status==='no_data'){
     cell.classList.add('no-data')
    }else if(info.actual_hours>0){
     if(info.overtime_100>0)cell.classList.add('has-ot100');else if(info.extra_hours>0)cell.classList.add('has-ot');
     if(info.partial_day&&info.d1_data_missing)cell.classList.add('both-warn');
     else if(info.partial_day)cell.classList.add('partial-day');
     else if(info.d1_data_missing)cell.classList.add('missing-punch');
     var toil=info.comment_toil||0,rawH=info.raw_hours||info.actual_hours,lines=[];
     lines.push('<div class="total-h">'+info.actual_hours.toFixed(2)+'h</div>');
     var bd='';
     if(toil>0){bd+='<span class="br-w">'+rawH.toFixed(2)+' worked</span><br><span class="br-toil">'+toil.toFixed(2)+' recup TOIL</span>'}
     else if(info.worked>0){bd+='<span class="br-w">'+info.worked.toFixed(2)+' worked</span>'}
     if(info.extra_hours>0)bd+=(bd?'<br>':'')+'<span class="br-e">'+info.extra_hours.toFixed(2)+' extra h</span>';
     if(info.overtime_100>0)bd+=(bd?'<br>':'')+'<span class="br-o">'+info.overtime_100.toFixed(2)+' overtime</span>';
     if(bd)lines.push('<div class="breakdown">'+bd+'</div>');
     if(info.comment&&toil===0&&info.comment_needs_review)lines.push('<div class="comment-hint" title="'+he(info.comment)+'">NEEDS REVIEW</div>');
     else if(info.comment_label&&toil===0)lines.push('<div class="comment-hint" title="'+he(info.comment)+'">'+he(info.comment_label)+'</div>');
     else if(info.comment&&toil===0)lines.push('<div class="comment-hint" title="'+he(info.comment)+'">'+he(info.comment).substring(0,25)+'</div>');
     cell.innerHTML+='<div class="data-block">'+lines.join('')+'</div>';
     if(info.partial_day)cell.innerHTML+='<div class="warn-tag partial">不足'+info.std_hours.toFixed(1)+'h</div>';
     if(info.d1_data_missing)cell.innerHTML+='<div class="warn-tag miss-punch">缺打卡</div>'
    }
    if(info.source){
     var bc='man',bt='';
     if(info.source.indexOf('data1')>=0&&info.source.indexOf('partial')<0&&info.source.indexOf('WARN')<0){bc='sys';bt='SYSTEM'}
     else if(info.source.indexOf('WARN')>=0){bc='miss';bt='NO PUNCH'}
     else if(info.source.indexOf('fallback')>=0||info.source.indexOf('partial')>=0){bc='miss';bt='FALLBACK'}
     else{bc='man';bt='MANUAL'}
     cell.innerHTML+='<div class="source-badge '+bc+'">'+bt+'</div>'
    }
    if(isWE)cell.classList.add('weekend')
   }
   row.appendChild(cell)
  }
  body.appendChild(row)
 }
 var mbar=document.getElementById('monthlyBar'),ws=emp.weekly_summary,wh='<span style="font-size:11px;opacity:.7">周汇总:</span>';
 Object.entries(ws).sort(function(a,b){return a[0]-b[0]}).forEach(function(e){
  var wk=e[0],wd=e[1],pd=wd.partial_days&&wd.partial_days.length>0?' WARN '+wd.partial_days.length+'天':'';
  wh+='<span style="font-size:10px;margin-left:8px">W'+wk+': <span style="color:#a5d6a7">'+wd.worked+'h</span> + <span style="color:#ffcc80">TOIL'+wd.extra+'h</span> + <span style="color:#ff8a80">OT'+wd.ot100+'h</span>'+pd+'</span>'
 });
 wh+='<div class="ms-group"><div class="ms-item"><span class="ms-label">正常</span><span class="ms-value worked">'+emp.monthly_summary.total_worked+'h</span></div><div class="ms-item"><span class="ms-label">调休</span><span class="ms-value extra">'+emp.monthly_summary.total_extra+'h</span></div><div class="ms-item"><span class="ms-label">加班费</span><span class="ms-value ot">'+emp.monthly_summary.total_ot100+'h</span></div></div>';
 mbar.innerHTML=wh
}

function renderNotes(emp){
 var nc=document.getElementById('notesContent'),items=[];
 var md=getMD();
 for(var d=1;d<=md;d++){
  var info=emp.days[String(d)];if(!info)continue;
  if(info.status==='unknown_note')items.push({t:'alert',msg:d+'日: 未知标记 "'+(info.note_raw||'')+'" - 需人工确认'});
  if(info.comment_toil>0)items.push({t:'info',msg:d+'日: 含'+info.comment_toil+'h调休补足(TOIL), 实际上班'+info.raw_hours+'h+'+info.comment_toil+'h TOIL='+info.actual_hours+'h(满勤)'});
  if(info.comment_needs_review&&!info.comment_toil)items.push({t:'warn',msg:d+'日: 批注含recup无数额-'+he(info.comment||'')+'-需人工确认'});
  if(info.partial_day&&info.d1_data_missing)items.push({t:'alert',msg:d+'日: 不满勤('+info.actual_hours+'h<'+info.std_hours+'h)+异常缺卡-需重点核查'});
  else if(info.partial_day)items.push({t:'warn',msg:d+'日: 不满勤'+info.actual_hours+'h<标准'+info.std_hours+'h-需确认是否扣款'});
  else if(info.d1_data_missing)items.push({t:'alert',msg:d+'日: 有打卡习惯员工无系统打卡数据-需确认缺卡原因'});
  if(info.cross_day)items.push({t:'info',msg:d+'日: 存在跨日凌晨打卡(已自动处理)'})
 }
 if(items.length===0)items.push({t:'info',msg:'无异常。数据来源: '+(emp.has_any_data1?'系统+线下':'仅线下')});
 nc.innerHTML=items.map(function(i){return'<div class="note-item '+i.t+'">'+i.msg+'</div>'}).join('');
 document.getElementById('notes').classList.add('show')
}

function he(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
init();'''

    # Inject JS into HTML
    js_injected = (
        js
        .replace('__JSON__', jso)
        .replace('__MONTH_KEYS__', json.dumps(month_keys_ordered))
        .replace('__MONTH_LABELS__', json.dumps(month_labels))
        .replace('__DEFAULT_MKEY__', default_mkey)
        .replace('__COUNTRY_NAME__', country_name)
    )

    final_html = html.replace('__DATA_JSON__', js_injected)

    if output_path is None:
        output_path = os.path.join(os.path.dirname(data_sources[0][0]), 'attendance_calendar.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"HTML日历生成: {output_path} ({len(final_html)} bytes)")
    return output_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='多国考勤HTML日历生成（支持多月份）')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--input', action='append', dest='inputs', help='JSON数据文件路径（可多次指定）')
    parser.add_argument('--label', action='append', dest='labels', help='月份显示标签（与--input对应）')
    parser.add_argument('--output', help='输出HTML路径（可选）')

    args = parser.parse_args()

    sources = []

    if args.config:
        # Single month mode (backward compat)
        with open(args.config, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        output_dir = cfg['file_paths'].get('output_dir', 'output')
        if not os.path.isabs(output_dir):
            cfg_dir = os.path.dirname(os.path.abspath(args.config))
            output_dir = os.path.join(cfg_dir, output_dir)
        json_path = os.path.join(output_dir, 'attendance_data.json')
        if not os.path.exists(json_path):
            print(f"错误: 找不到JSON文件 {json_path}")
            sys.exit(1)
        yr = cfg.get('year', 2026)
        mo = cfg.get('month', 6)
        sources.append((json_path, f"{yr}年{mo}月"))
    elif args.inputs:
        labels = args.labels or []
        for i, inp in enumerate(args.inputs):
            if not os.path.exists(inp):
                # Try to resolve relative to script dir
                resolved = os.path.join(os.path.dirname(os.path.abspath(__file__)), inp)
                if not os.path.exists(resolved):
                    print(f"错误: 找不到JSON文件 {inp}")
                    sys.exit(1)
                inp = resolved
            label = labels[i] if i < len(labels) else None
            sources.append((inp, label))
    else:
        # Default: try single file
        json_path = 'output/attendance_data.json'
        if not os.path.exists(json_path):
            print("错误: 找不到JSON文件，请指定 --input")
            sys.exit(1)
        sources.append((json_path, None))

    if len(sources) == 0:
        print("错误: 未指定数据源")
        sys.exit(1)

    build_html(sources, args.output)
