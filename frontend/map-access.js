function renderRiskMap(){
  const located=incidents.filter(x=>Number.isFinite(x.latitude)&&Number.isFinite(x.longitude));
  if(!located.length){
    $("mapBoard").innerHTML=empty("Add consent based coordinates to a new report to display it here.");
    $("mapList").innerHTML=empty("No mapped locations yet.");
    return;
  }
  const lats=located.map(x=>x.latitude),lons=located.map(x=>x.longitude);
  const minLat=Math.min(...lats),maxLat=Math.max(...lats),minLon=Math.min(...lons),maxLon=Math.max(...lons);
  $("mapBoard").innerHTML=located.map(x=>{
    const left=maxLon===minLon?50:8+84*(x.longitude-minLon)/(maxLon-minLon);
    const top=maxLat===minLat?50:8+84*(maxLat-x.latitude)/(maxLat-minLat);
    return `<button class="marker ${x.risk_level.toLowerCase()}" style="left:${left}%;top:${top}%" title="${esc(x.location_name)}: ${x.risk_level}" aria-label="${esc(x.location_name)}, ${x.risk_level}"></button>`;
  }).join("");
  const grouped=Object.values(located.reduce((all,x)=>{
    all[x.location_name]??={name:x.location_name,total:0,priority:0,review:0};
    all[x.location_name].total++;
    all[x.location_name][x.risk_level.toLowerCase()]++;
    return all;
  },{}));
  $("mapList").innerHTML=grouped.map(x=>`<div class="mapsummary"><b>${esc(x.name)}</b><span>${x.total} report${x.total===1?"":"s"} · ${x.priority?"Priority":""}${x.priority&&x.review?" and ":""}${x.review?"Review":""}${!x.priority&&!x.review?"Routine":""}</span></div>`).join("");
}

const roleAccess={
  "Administrator":["Manage users and assigned sites","View operational summaries","Configure approved thresholds","Review audit activity"],
  "Occupational Health Officer":["Record screening flags","Review assigned health cases","Document professional action","View deidentified trends"],
  "Mine Safety Officer":["Create and review safety reports","Assign corrective actions","Update case status","View site risk summaries"],
  "Environmental Officer":["Record environmental measurements","Review threshold flags","View environmental locations","Prepare monitoring summaries"],
  "Community Relations Officer":["Record community concerns","Track approved follow up","View community summaries","No occupational health details"],
  "Management Viewer":["View aggregated dashboards","View approved reports","No editing permissions","No individual health details"],
  "Data Analyst":["View deidentified datasets","Generate approved summaries","Run data quality checks","No user administration"],
  "Regulatory Observer":["View approved compliance summaries","View closed action evidence","Read only access","No personal health records"]
};
function showRole(){const role=$("roleSelect").value;$("roleSummary").innerHTML=`<p class="eyebrow">${esc(role)}</p><h3>Permitted workspace</h3><ul>${roleAccess[role].map(x=>`<li>${x}</li>`).join("")}</ul><p class="notice">Preview only. Production access must be checked by the backend for every request.</p>`}
$("roleSelect").onchange=showRole;showRole();
const baseRender=window.render;
window.render=function(){baseRender();renderRiskMap()};
renderRiskMap();
