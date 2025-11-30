import React, {useState} from "react";

function App(){
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const login = async()=>{
    const data = new URLSearchParams();
    data.append("username", email);
    data.append("password", password);
    const res = await fetch("http://localhost:8000/auth/login", {method:"POST", body:data});
    const json = await res.json();
    if(json.access_token){
      setToken(json.access_token);
      alert("Logged in");
    } else {
      alert("Login failed");
    }
  }
  return (<div style={{fontFamily:"sans-serif", padding:20}}>
    <h2>Payroll Demo (MVP)</h2>
    <p>Seeded admin: hire-me@anshumat.org / HireMe@2025!</p>
    {!token ? (
      <div style={{maxWidth:360}}>
        <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} style={{width:"100%", padding:8, marginBottom:8}}/>
        <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} style={{width:"100%", padding:8, marginBottom:8}}/>
        <button onClick={login} style={{padding:8}}>Login</button>
      </div>
    ) : (
      <div>
        <p>Authenticated. You can use API via /docs (backend) or extend frontend.</p>
      </div>
    )}
  </div>)
}

export default App;
