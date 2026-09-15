(function(){
  const configured=window.TRAFFICAGENT_CONFIG||{};
  const api=(configured.API_BASE_URL||'http://localhost:8080').replace(/\/$/,'');
  const token=()=>localStorage.getItem('traficcagent-access-token')||localStorage.getItem('access_token');
  const tenant=()=>localStorage.getItem('traficcagent-active-tenant');
  window.TrafficAgentCore={
    api,
    headers:()=>({Authorization:'Bearer '+(token()||''),'Content-Type':'application/json'}),
    context:()=>fetch(api+'/api/context',{headers:window.TrafficAgentCore.headers()}).then(r=>r.ok?r.json():Promise.reject(r)),
    summary:(dimension='Site',environment='Operação')=>fetch(api+'/api/operacao/resumo?tenant_id='+encodeURIComponent(tenant()||'')+'&dimensao='+encodeURIComponent(dimension)+'&ambiente='+encodeURIComponent(environment),{headers:window.TrafficAgentCore.headers()}).then(r=>r.ok?r.json():Promise.reject(r)),
    catalog:(type='site')=>fetch(api+'/api/operacao/catalogo?tenant_id='+encodeURIComponent(tenant()||'')+'&tipo='+encodeURIComponent(type),{headers:window.TrafficAgentCore.headers()}).then(r=>r.ok?r.json():Promise.reject(r)),
    event:(payload)=>fetch(api+'/api/operacao/eventos',{method:'POST',headers:window.TrafficAgentCore.headers(),body:JSON.stringify(Object.assign({tenant_id:Number(tenant()||0)},payload))}).then(r=>r.ok),
    isAuthenticated:()=>Boolean(token()&&tenant())
  };
})();
