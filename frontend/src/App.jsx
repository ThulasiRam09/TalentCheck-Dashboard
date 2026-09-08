import React, { useState, useEffect } from 'react';
import { 
  User, Mail, GraduationCap, Award, FileCode, CheckCircle, 
  Trash2, Plus, Zap, Code, Shield, Briefcase, HelpCircle, 
  ChevronRight, RefreshCw, Layers, Compass, Play, FileJson, Upload, FileText
} from 'lucide-react';
import { extractTextFromFile } from './lib/fileExtract';

const API_BASE = 'https://talentcheck-dashboard-5.onrender.com/api';

const CATEGORY_MAP = {
  "COD": "Coding (COD)",
  "DSA": "Data Structures & Algos (DSA)",
  "OOD": "Object Oriented Design (OOD)",
  "APTI": "Quantitative Aptitude (APTI)",
  "COMM": "Communication Skills (COMM)",
  "AI": "Artificial Intelligence / ML (AI)",
  "CLOUD": "Cloud Computing (CLOUD)",
  "SQL": "SQL & Databases (SQL)",
  "SWE": "Software Engineering (SWE)",
  "SYSD": "System Design (SYSD)",
  "NETW": "Networking (NETW)",
  "OS": "Operating Systems (OS)",
  "OTHER": "Other Skills"
};

function App() {
  const [activeTab, setActiveTab] = useState('resume');
  const [companies, setCompanies] = useState([]);
  const [sampleProfiles, setSampleProfiles] = useState([]);
  const [activeProfileId, setActiveProfileId] = useState('');
  
  // Profile Form States
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [education, setEducation] = useState('');
  const [preferredRoles, setPreferredRoles] = useState([]);
  const [skills, setSkills] = useState([]);
  const [hackathons, setHackathons] = useState([]);
  const [internships, setInternships] = useState([]);
  const [certifications, setCertifications] = useState([]);
  
  // File upload states
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [analyzedJd, setAnalyzedJd] = useState(null);
  const [skillMatchResult, setSkillMatchResult] = useState(null);
  
  // Target evaluation company
  const [selectedCompany, setSelectedCompany] = useState('');

  // Form input temporary states
  const [tempRole, setTempRole] = useState('');
  const [tempHackathon, setTempHackathon] = useState('');
  const [tempInternship, setTempInternship] = useState('');
  const [tempCertification, setTempCertification] = useState('');
  const [tempSkill, setTempSkill] = useState({
    skill_name: '',
    category_code: 'COD',
    confidence: 'medium'
  });

  // Loading States
  const [loading, setLoading] = useState(false);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [jdLoading, setJdLoading] = useState(false);
  const [matchLoading, setMatchLoading] = useState(false);
  
  // Result and Error States
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [resumeSuccess, setResumeSuccess] = useState('');

  // Fetch companies and sample profiles on load
  useEffect(() => {
    fetchCompanies();
    fetchSampleProfiles();
  }, []);

  const fetchCompanies = async () => {
    try {
      const res = await fetch(`${API_BASE}/companies`);
      if (res.ok) {
        const data = await res.json();
        setCompanies(data);
        if (data.length > 0) setSelectedCompany(data[0].name);
      } else {
        setError('Failed to load companies from backend server.');
      }
    } catch (e) {
      setError('Could not connect to backend server. Make sure server.py is running on port 8000!');
    }
  };

  const fetchSampleProfiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/profiles`);
      if (res.ok) {
        const data = await res.json();
        setSampleProfiles(data);
      }
    } catch (e) {
      console.error("Error fetching profiles:", e);
    }
  };

  const applyProfilePrefill = (prof) => {
    setActiveProfileId(prof.id);
    setName(prof.name);
    setEmail(prof.email);
    setEducation(prof.education);
    setPreferredRoles(prof.preferred_roles || []);
    setSkills(prof.skills || []);
    setHackathons(prof.hackathons || []);
    setInternships(prof.internships || []);
    setCertifications(prof.certifications || []);
    setResumeSuccess('Prefilled simulator profile loaded successfully!');
  };

  // Helper to add skill
  const handleAddSkill = (e) => {
    e.preventDefault();
    if (!tempSkill.skill_name.trim()) return;
    
    if (skills.some(s => s.skill_name.toLowerCase() === tempSkill.skill_name.trim().toLowerCase())) {
      alert("This skill is already added.");
      return;
    }

    setSkills([...skills, { ...tempSkill, skill_name: tempSkill.skill_name.trim() }]);
    setTempSkill({ ...tempSkill, skill_name: '' });
  };

  // Helper to remove items
  const removeSkill = (index) => setSkills(skills.filter((_, i) => i !== index));
  const removeRole = (index) => setPreferredRoles(preferredRoles.filter((_, i) => i !== index));
  const removeHackathon = (index) => setHackathons(hackathons.filter((_, i) => i !== index));
  const removeInternship = (index) => setInternships(internships.filter((_, i) => i !== index));
  const removeCertification = (index) => setCertifications(certifications.filter((_, i) => i !== index));

  // Resume Parsing Handlers
  const handleResumeFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setResumeFile(file);
    setResumeLoading(true);
    setError('');
    setResumeSuccess('');
    try {
      const text = await extractTextFromFile(file);
      const res = await fetch(`${API_BASE}/parse-resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, text: text })
      });
      if (res.ok) {
        const parsedProfile = await res.json();
        setName(parsedProfile.name || '');
        setEmail(parsedProfile.email || '');
        setEducation(parsedProfile.education || '');
        setPreferredRoles(parsedProfile.preferred_roles || []);
        setSkills(parsedProfile.skills || []);
        setHackathons(parsedProfile.hackathons || []);
        setInternships(parsedProfile.internships || []);
        setCertifications(parsedProfile.certifications || []);
        setResumeSuccess(`Successfully parsed ${file.name}! Profile builder has been auto-populated.`);
        setActiveProfileId('parsed');
        setTimeout(() => setActiveTab('profile'), 1500); // Redirect to Profile Builder
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to parse resume with AI model.');
      }
    } catch (err) {
      setError(err.message || 'Error processing resume file.');
    } finally {
      setResumeLoading(false);
    }
  };

  // JD Analysis Handlers
  const handleJdFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setJdFile(file);
    setJdLoading(true);
    setError('');
    try {
      const text = await extractTextFromFile(file);
      const res = await fetch(`${API_BASE}/analyze-jd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, text: text })
      });
      if (res.ok) {
        const analyzed = await res.json();
        setAnalyzedJd(analyzed);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to analyze JD with AI model.');
      }
    } catch (err) {
      setError(err.message || 'Error processing Job Description file.');
    } finally {
      setJdLoading(false);
    }
  };

  // Run matching check (Talent Check)
  const handleRunCheck = async () => {
    if (!name.trim()) {
      alert("Please enter candidate name in Profile Builder.");
      setActiveTab('profile');
      return;
    }
    if (!selectedCompany) {
      alert("Please select a target company.");
      return;
    }

    setLoading(true);
    setError('');
    try {
      const payload = {
        profile: {
          name,
          email,
          education,
          skills,
          hackathons,
          internships,
          certifications,
          preferred_roles: preferredRoles
        },
        company: selectedCompany
      };

      const res = await fetch(`${API_BASE}/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
        setActiveTab('check');
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Server error running evaluation.');
      }
    } catch (e) {
      setError('Connection to assessment engine failed. Verify server.py is running!');
    } finally {
      setLoading(false);
    }
  };

  // Run ATS Skill Match
  const handleRunSkillMatch = async () => {
    if (!name.trim()) {
      alert("Please enter candidate name in Profile Builder.");
      setActiveTab('profile');
      return;
    }
    if (!analyzedJd) {
      alert("Please upload and analyze a Job Description first.");
      setActiveTab('jd');
      return;
    }

    setMatchLoading(true);
    setError('');
    try {
      const payload = {
        profile: {
          name,
          email,
          education,
          skills,
          hackathons,
          internships,
          certifications,
          preferred_roles: preferredRoles
        },
        jd: analyzedJd
      };

      const res = await fetch(`${API_BASE}/skill-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setSkillMatchResult(data);
        setActiveTab('match');
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Server error calculating match.');
      }
    } catch (e) {
      setError('Skill match API connection failed.');
    } finally {
      setMatchLoading(false);
    }
  };

  // Render Resume Tab
  const renderResumeTab = () => (
    <div className="tab-content">
      <div className="prefill-section">
        <h3 className="prefill-title">
          <Layers size={18} /> Or select a Simulation Candidate Profile
        </h3>
        <div className="prefill-cards">
          {sampleProfiles.map(prof => (
            <div 
              key={prof.id} 
              className={`prefill-card ${activeProfileId === prof.id ? 'active' : ''}`}
              onClick={() => applyProfilePrefill(prof)}
            >
              <div>
                <div className="prefill-name">{prof.name}</div>
                <div className="prefill-edu">{prof.education}</div>
              </div>
              <div className="prefill-stats">
                <span className="prefill-stat-badge">{prof.skills?.length || 0} Skills</span>
                <span className="prefill-stat-badge">{prof.internships?.length || 0} Exp</span>
                <span className="prefill-stat-badge">{prof.certifications?.length || 0} Certs</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ maxWidth: '600px', margin: '2rem auto 0 auto' }}>
        <h2 className="card-title" style={{ justifyContent: 'center' }}>
          <Upload size={20} className="text-green" /> Upload Candidate Resume
        </h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          Drop candidate CV/Resume (PDF, DOCX, TXT) here. Our AI engine will parse contact details, experience, certifications, hackathons, and categorize technical/soft skills automatically.
        </p>

        <label className="dropzone-container">
          <input 
            type="file" 
            accept=".pdf,.docx,.txt" 
            onChange={handleResumeFileChange} 
            style={{ display: 'none' }}
          />
          <Upload size={40} className="dropzone-icon" />
          <div className="dropzone-text">Click to browse or drop resume file here</div>
          <div className="dropzone-subtext">Supports PDF, DOCX, or Plain Text up to 10MB</div>
        </label>

        {resumeLoading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem', color: 'var(--accent-cyan)' }}>
            <RefreshCw className="animate-spin" size={18} />
            <span>AI parsing and mapping skills to RADIX matrix...</span>
          </div>
        )}

        {resumeSuccess && (
          <div style={{ color: 'var(--accent-green)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', marginTop: '1.5rem', fontSize: '0.95rem', fontWeight: 600 }}>
            <CheckCircle size={16} />
            <span>{resumeSuccess}</span>
          </div>
        )}
      </div>
    </div>
  );

  // Profile Builder Tab Content
  const renderProfileTab = () => (
    <div className="tab-content">
      <div className="form-grid">
        {/* Left Card: Basic Details and Experience */}
        <div className="card">
          <h2 className="card-title">
            <User size={20} className="text-green" /> Profile & Experience
          </h2>
          
          <div className="form-row">
            <div className="form-group">
              <label>Full Name</label>
              <input 
                type="text" 
                placeholder="e.g. John Doe"
                value={name}
                onChange={e => setName(e.target.value)} 
              />
            </div>
            <div className="form-group">
              <label>Email Address</label>
              <input 
                type="email" 
                placeholder="e.g. john@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)} 
              />
            </div>
          </div>

          <div className="form-group">
            <label>Education</label>
            <input 
              type="text" 
              placeholder="e.g. BS Computer Science, Stanford University"
              value={education}
              onChange={e => setEducation(e.target.value)} 
            />
          </div>

          {/* Preferred Roles list */}
          <div className="form-group">
            <label>Preferred Roles</label>
            <div className="items-list-container">
              <div className="items-input-row">
                <input 
                  type="text" 
                  placeholder="e.g. Backend Engineer"
                  value={tempRole}
                  onChange={e => setTempRole(e.target.value)}
                  onKeyDown={e => { if(e.key === 'Enter') { e.preventDefault(); if(tempRole.trim()) { setPreferredRoles([...preferredRoles, tempRole.trim()]); setTempRole(''); } } }}
                />
                <button 
                  type="button" 
                  className="add-btn" 
                  onClick={() => { if(tempRole.trim()) { setPreferredRoles([...preferredRoles, tempRole.trim()]); setTempRole(''); } }}
                >
                  <Plus size={16} />
                </button>
              </div>
              <div className="badges-grid">
                {preferredRoles.map((role, idx) => (
                  <span key={idx} className="item-badge">
                    {role}
                    <button type="button" onClick={() => removeRole(idx)}><Trash2 size={12} /></button>
                  </span>
                ))}
                {preferredRoles.length === 0 && <span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>No preferred roles added.</span>}
              </div>
            </div>
          </div>

          {/* Internships list */}
          <div className="form-group">
            <label>Internships / Work History</label>
            <div className="items-list-container">
              <div className="items-input-row">
                <input 
                  type="text" 
                  placeholder="e.g. Software Engineer Intern @ Google"
                  value={tempInternship}
                  onChange={e => setTempInternship(e.target.value)}
                  onKeyDown={e => { if(e.key === 'Enter') { e.preventDefault(); if(tempInternship.trim()) { setInternships([...internships, tempInternship.trim()]); setTempInternship(''); } } }}
                />
                <button 
                  type="button" 
                  className="add-btn" 
                  onClick={() => { if(tempInternship.trim()) { setInternships([...internships, tempInternship.trim()]); setTempInternship(''); } }}
                >
                  <Plus size={16} />
                </button>
              </div>
              <div className="list-items-vertical">
                {internships.map((intern, idx) => (
                  <div key={idx} className="list-item-pill">
                    <span className="text-secondary" style={{fontSize: '0.9rem'}}>{intern}</span>
                    <button type="button" onClick={() => removeInternship(idx)} className="delete-pill-btn"><Trash2 size={14} /></button>
                  </div>
                ))}
                {internships.length === 0 && <span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>No internships added.</span>}
              </div>
            </div>
          </div>

          {/* Hackathons list */}
          <div className="form-group">
            <label>Hackathons Participated</label>
            <div className="items-list-container">
              <div className="items-input-row">
                <input 
                  type="text" 
                  placeholder="e.g. Stanford TreeHacks 2024"
                  value={tempHackathon}
                  onChange={e => setTempHackathon(e.target.value)}
                  onKeyDown={e => { if(e.key === 'Enter') { e.preventDefault(); if(tempHackathon.trim()) { setHackathons([...hackathons, tempHackathon.trim()]); setTempHackathon(''); } } }}
                />
                <button 
                  type="button" 
                  className="add-btn" 
                  onClick={() => { if(tempHackathon.trim()) { setHackathons([...hackathons, tempHackathon.trim()]); setTempHackathon(''); } }}
                >
                  <Plus size={16} />
                </button>
              </div>
              <div className="list-items-vertical">
                {hackathons.map((hack, idx) => (
                  <div key={idx} className="list-item-pill">
                    <span className="text-secondary" style={{fontSize: '0.9rem'}}>{hack}</span>
                    <button type="button" onClick={() => removeHackathon(idx)} className="delete-pill-btn"><Trash2 size={14} /></button>
                  </div>
                ))}
                {hackathons.length === 0 && <span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>No hackathons added.</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Right Card: Skills and Certifications */}
        <div className="card">
          <h2 className="card-title">
            <Award size={20} className="text-green" /> Skills & Certifications
          </h2>

          {/* Certifications list */}
          <div className="form-group">
            <label>Professional Certifications</label>
            <div className="items-list-container">
              <div className="items-input-row">
                <input 
                  type="text" 
                  placeholder="e.g. AWS Certified Developer"
                  value={tempCertification}
                  onChange={e => setTempCertification(e.target.value)}
                  onKeyDown={e => { if(e.key === 'Enter') { e.preventDefault(); if(tempCertification.trim()) { setCertifications([...certifications, tempCertification.trim()]); setTempCertification(''); } } }}
                />
                <button 
                  type="button" 
                  className="add-btn" 
                  onClick={() => { if(tempCertification.trim()) { setCertifications([...certifications, tempCertification.trim()]); setTempCertification(''); } }}
                >
                  <Plus size={16} />
                </button>
              </div>
              <div className="badges-grid">
                {certifications.map((cert, idx) => (
                  <span key={idx} className="item-badge purple">
                    {cert}
                    <button type="button" onClick={() => removeCertification(idx)}><Trash2 size={12} /></button>
                  </span>
                ))}
                {certifications.length === 0 && <span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>No certifications added.</span>}
              </div>
            </div>
          </div>

          <div style={{borderBottom: '1px solid var(--border-color)', margin: '1.5rem 0'}} />

          {/* Skills builder */}
          <div className="form-group">
            <label style={{fontWeight: 600, display: 'flex', alignItems: 'center', justifyBetween: 'space-between', width: '100%'}}>
              <span>Candidate Skill List ({skills.length})</span>
            </label>
            
            <form onSubmit={handleAddSkill} className="skill-adder-container">
              <div className="skill-input-grid">
                <input 
                  type="text" 
                  placeholder="Skill (e.g. PyTorch, React, Java)"
                  value={tempSkill.skill_name}
                  onChange={e => setTempSkill({ ...tempSkill, skill_name: e.target.value })}
                />
                <select 
                  value={tempSkill.category_code}
                  onChange={e => setTempSkill({ ...tempSkill, category_code: e.target.value })}
                >
                  {Object.entries(CATEGORY_MAP).map(([code, label]) => (
                    <option key={code} value={code}>{label}</option>
                  ))}
                </select>
                <select 
                  value={tempSkill.confidence}
                  onChange={e => setTempSkill({ ...tempSkill, confidence: e.target.value })}
                >
                  <option value="high">High Confidence (3+ yrs)</option>
                  <option value="medium">Medium (1-2 yrs)</option>
                  <option value="low">Low (Theory/Basic)</option>
                </select>
              </div>
              <button type="submit" className="add-btn skill-add-btn">
                <Plus size={16} /> Add Skill to Profile
              </button>
            </form>

            {/* Render added skills */}
            <div className="added-skills-container">
              {skills.map((skill, idx) => (
                <div key={idx} className="skill-row-item">
                  <div className="skill-name-col">
                    <span className="skill-bullet" />
                    <strong>{skill.skill_name}</strong>
                  </div>
                  <span className="skill-cat-label">
                    {CATEGORY_MAP[skill.category_code] || skill.category_code}
                  </span>
                  <span className={`skill-confidence-badge ${skill.confidence}`}>
                    {skill.confidence.toUpperCase()}
                  </span>
                  <button type="button" onClick={() => removeSkill(idx)} className="delete-pill-btn">
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {skills.length === 0 && (
                <div style={{color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic', padding: '1rem', textAlign: 'center'}}>
                  No skills added. Enter candidate skills using the form above or upload a resume.
                </div>
              )}
            </div>
          </div>

          <div style={{borderBottom: '1px solid var(--border-color)', margin: '1.5rem 0'}} />

          <div style={{ display: 'flex', gap: '1rem' }}>
            <button 
              type="button" 
              className="action-btn-green"
              onClick={handleRunCheck}
              style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontWeight: 600}}
            >
              <Play size={16} /> Run Talent Check Report
            </button>
            
            <button 
              type="button" 
              className="action-btn-green"
              disabled={!analyzedJd}
              onClick={handleRunSkillMatch}
              style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontWeight: 600, opacity: analyzedJd ? 1 : 0.5}}
            >
              <FileCode size={16} /> Run ATS Skill Match
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // JD Analytics Tab Content
  const renderJdTab = () => (
    <div className="tab-content">
      <div className="card" style={{ maxWidth: '600px', margin: '0 auto 2rem auto' }}>
        <h2 className="card-title" style={{ justifyContent: 'center' }}>
          <Upload size={20} className="text-green" /> Upload Job Description (JD)
        </h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          Upload the target job description (PDF, DOCX, TXT). The system extracts technical skills, technologies, experience limits, responsibilities, and seniority to perform direct compatibility audits.
        </p>

        <label className="dropzone-container">
          <input 
            type="file" 
            accept=".pdf,.docx,.txt" 
            onChange={handleJdFileChange} 
            style={{ display: 'none' }}
          />
          <FileText size={40} className="dropzone-icon" />
          <div className="dropzone-text">Click to browse or drop Job Description here</div>
          <div className="dropzone-subtext">Supports PDF, DOCX, or Plain Text up to 10MB</div>
        </label>

        {jdLoading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem', color: 'var(--accent-cyan)' }}>
            <RefreshCw className="animate-spin" size={18} />
            <span>AI analyzing and extracting role requirements...</span>
          </div>
        )}
      </div>

      {analyzedJd ? (
        <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>ROLE SPECIFICATIONS</span>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 700, marginTop: '0.2rem' }}>{analyzedJd.seniority} {analyzedJd.location ? `· ${analyzedJd.location}` : ''}</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.2rem' }}>Type: {analyzedJd.job_type} | Experience: {analyzedJd.experience}</p>
            </div>
            <span className="tag met" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>ANALYZED</span>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Summary</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6' }}>{analyzedJd.summary}</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Required Skills</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {analyzedJd.skills?.map((s, i) => (
                  <span key={i} className="item-badge" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.2)' }}>{s}</span>
                ))}
              </div>
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Technologies & Frameworks</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {analyzedJd.technologies?.map((s, i) => (
                  <span key={i} className="item-badge purple">{s}</span>
                ))}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Responsibilities</h3>
            <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.95rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {analyzedJd.responsibilities?.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
            <button 
              className="action-btn-green"
              onClick={handleRunSkillMatch}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}
            >
              <FileCode size={18} /> Run Compatibility Skill Match
            </button>
          </div>
        </div>
      ) : (
        <div className="empty-state" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <HelpCircle size={48} className="empty-icon" />
          <h2>No Job Description Analyzed</h2>
          <p className="empty-text">Upload a job posting to extract requirements and proceed to Skill Matching.</p>
        </div>
      )}
    </div>
  );

  // Talent Check Evaluation Dashboard
  const renderEvaluationTab = () => {
    if (!result) {
      return (
        <div className="empty-state">
          <HelpCircle size={48} className="empty-icon" />
          <h2>No Assessment Run Yet</h2>
          <p className="empty-text">
            Build a candidate profile first, then select a company and press the "Run Talent Check" button to see the gap analysis report.
          </p>
          <button className="add-btn" onClick={() => setActiveTab('profile')} style={{marginTop: '1rem'}}>
            Go to Profile Builder
          </button>
        </div>
      );
    }

    const scoreColorClass = 
      result.readiness_score >= 85 ? 'score-green' : 
      result.readiness_score >= 70 ? 'score-yellow' : 
      result.readiness_score >= 50 ? 'score-orange' : 'score-red';

    const circumference = 2 * Math.PI * 22; // r=22
    const strokeDash = (result.readiness_score / 100) * circumference;

    return (
      <div className="tab-content">
        <div className="results-grid">
          {/* Left Panel: Circular readiness score & highlights */}
          <div className="score-panel">
            <h2 style={{fontSize: '1.4rem', fontWeight: 600, marginBottom: '1.5rem'}}>Match Evaluation</h2>
            
            {/* Score Ring */}
            <svg viewBox="0 0 50 50" className="circular-chart">
              <circle className="circle-bg" cx="25" cy="25" r="22" />
              <path className={`circle ${scoreColorClass}`}
                strokeDasharray={`${strokeDash}, ${circumference}`}
                d="M25 3 a 22 22 0 0 1 0 44 a 22 22 0 0 1 0 -44"
              />
              <text x="25" y="28" className="percentage">{Math.round(result.readiness_score)}%</text>
            </svg>

            {/* Overall status badge */}
            <div className={`status-badge ${result.overall_readiness.toLowerCase().replace(' ', '_')}`}>
              {result.overall_readiness.toUpperCase()}
            </div>

            {/* Assessment Text Box */}
            <p style={{color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '1.5rem 0 0.5rem', lineHeight: '1.5'}}>
              {result.summary}
            </p>

            <div style={{borderBottom: '1px solid var(--border-color)', width: '100%', margin: '1.5rem 0'}} />

            {/* Applied experience highlights panel */}
            <div style={{textAlign: 'left', width: '100%'}}>
              <h3 style={{fontSize: '1rem', fontWeight: 600, color: 'var(--accent-magenta)', marginBottom: '0.75rem'}}>
                Experience & Certification Boosts
              </h3>
              
              <div style={{display: 'flex', flexDirection: 'column', gap: '0.6rem'}}>
                {internships.length > 0 ? (
                  <div className="badge-skill-level">
                    <Briefcase size={15} className="text-green" />
                    <span style={{fontSize: '0.9rem'}}>
                      {internships.length} Internship(s) applied (+{Math.min(10, internships.length * 3.0)}% overall boost)
                    </span>
                  </div>
                ) : null}

                {hackathons.length > 0 ? (
                  <div className="badge-skill-level">
                    <Zap size={15} className="text-green" />
                    <span style={{fontSize: '0.9rem'}}>
                      {hackathons.length} Hackathon(s) applied (+{Math.min(5, hackathons.length * 1.5)}% overall boost)
                    </span>
                  </div>
                ) : null}

                {certifications.length > 0 ? (
                  <div className="badge-skill-level">
                    <Award size={15} className="text-green" />
                    <span style={{fontSize: '0.9rem'}}>
                      Certifications scanned ({certifications.length}) and skill categories boosted (+2 skill levels)
                    </span>
                  </div>
                ) : null}

                {internships.length === 0 && hackathons.length === 0 && certifications.length === 0 && (
                  <div style={{color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic'}}>
                    No experience boosts applied. Add certifications, hackathons, or internships to raise your readiness score.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Panel: Detailed gaps table */}
          <div className="card">
            <h2 className="card-title">
              <Layers size={20} className="text-green" /> Skillset Gap Analysis
            </h2>
            
            <div style={{overflowX: 'auto'}}>
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th style={{textAlign: 'center'}}>Required</th>
                    <th style={{textAlign: 'center'}}>Candidate</th>
                    <th>Status / Visual Level</th>
                  </tr>
                </thead>
                <tbody>
                  {result.skillset_gap.map((gap, idx) => {
                    const required = gap.required_level;
                    const candidate = gap.candidate_level;
                    const fillPercent = (candidate / 10) * 100;
                    
                    const barColor = 
                      candidate >= required ? 'var(--accent-green)' : 
                      candidate >= 5 ? 'var(--accent-yellow)' : 'var(--accent-red)';

                    return (
                      <tr key={idx}>
                        <td style={{fontWeight: 500, fontSize: '0.95rem'}}>
                          {CATEGORY_MAP[gap.category] || gap.category}
                        </td>
                        <td style={{textAlign: 'center', fontSize: '0.95rem'}}>{required}/10</td>
                        <td style={{textAlign: 'center', fontSize: '0.95rem', fontWeight: 600}}>{candidate}/10</td>
                        <td>
                          <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                            <span className={`tag ${gap.gap ? 'gap' : 'met'}`}>
                              {gap.gap ? 'GAP' : 'MET'}
                            </span>
                            <div className="visual-bar-bg">
                              <div className="visual-bar-fill" style={{width: `${fillPercent}%`, backgroundColor: barColor}} />
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Actionable recommendations at bottom */}
        <div className="card" style={{marginTop: '2rem'}}>
          <h2 className="card-title" style={{color: 'var(--accent-yellow)', borderBottomColor: 'rgba(245, 158, 11, 0.2)'}}>
            <Shield size={20} className="text-yellow" /> Recommended Career Pathways
          </h2>
          <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
            {result.recommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-item">
                <CheckCircle size={16} className={rec.includes("Improve") ? "text-yellow rec-icon" : "text-green rec-icon"} />
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Skill Matching Tab Content
  const renderSkillMatchTab = () => {
    if (!skillMatchResult) {
      return (
        <div className="empty-state">
          <HelpCircle size={48} className="empty-icon" />
          <h2>No Skill Matching Performed</h2>
          <p className="empty-text">
            Upload and analyze a Job Description in the JD Analytics tab first, build a candidate profile, then press the "Run ATS Skill Match" button.
          </p>
          {analyzedJd ? (
            <button className="add-btn" onClick={handleRunSkillMatch} style={{marginTop: '1rem'}}>
              Run Skill Match
            </button>
          ) : (
            <button className="add-btn" onClick={() => setActiveTab('jd')} style={{marginTop: '1rem'}}>
              Go to JD Analytics
            </button>
          )}
        </div>
      );
    }

    const tc = skillMatchResult;
    const scoreColorClass = 
      tc.match_score >= 85 ? 'score-green' : 
      tc.match_score >= 70 ? 'score-yellow' : 
      tc.match_score >= 50 ? 'score-orange' : 'score-red';

    const circumference = 2 * Math.PI * 22; // r=22
    const strokeDash = (tc.match_score / 100) * circumference;

    return (
      <div className="tab-content">
        <div className="results-grid">
          {/* Left Panel: Circular compatibility score */}
          <div className="score-panel">
            <h2 style={{fontSize: '1.4rem', fontWeight: 600, marginBottom: '1.5rem'}}>ATS Match Compatibility</h2>
            
            {/* Score Ring */}
            <svg viewBox="0 0 50 50" className="circular-chart">
              <circle className="circle-bg" cx="25" cy="25" r="22" />
              <path className={`circle ${scoreColorClass}`}
                strokeDasharray={`${strokeDash}, ${circumference}`}
                d="M25 3 a 22 22 0 0 1 0 44 a 22 22 0 0 1 0 -44"
              />
              <text x="25" y="28" className="percentage">{Math.round(tc.match_score)}%</text>
            </svg>

            {/* Eligibility Badge */}
            <div style={{ marginTop: '1.5rem' }}>
              <span className={`eligibility-badge eligibility-${tc.eligibility.toLowerCase().replace(' ', '-')}`}>
                {tc.eligibility.toUpperCase()}
              </span>
            </div>

            <p style={{color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '1.5rem 0 0.5rem', lineHeight: '1.6', textAlign: 'center'}}>
              Role: <strong>{tc.role}</strong><br/>
              Company: <strong>{tc.company}</strong>
            </p>
          </div>

          {/* Right Panel: Skill breakdown breakdown */}
          <div className="card">
            <h2 className="card-title">
              <Layers size={20} className="text-green" /> Skills Compatibility Audit
            </h2>

            {/* Matched Skills */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-green)', marginBottom: '0.5rem' }}>
                Directly Matched Skills ({tc.matched_skills?.length || 0})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {tc.matched_skills?.map((s, i) => (
                  <span key={i} className="item-badge" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.2)' }}>{s}</span>
                ))}
                {(!tc.matched_skills || tc.matched_skills.length === 0) && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None.</span>}
              </div>
            </div>

            {/* Partial / Fuzzy Matches */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-yellow)', marginBottom: '0.5rem' }}>
                Fuzzy Matches / Closely Related Skills ({tc.partial_matches?.length || 0})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {tc.partial_matches?.map((pm, i) => (
                  <div key={i} className="list-item-pill" style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.15)' }}>
                    <span style={{ fontSize: '0.85rem' }}>Candidate <strong>{pm.candidate_skill}</strong> matches JD <strong>{pm.jd_skill}</strong></span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--accent-yellow)', fontWeight: 600 }}>{pm.similarity}% Sim</span>
                  </div>
                ))}
                {(!tc.partial_matches || tc.partial_matches.length === 0) && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None.</span>}
              </div>
            </div>

            {/* Missing Skills */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-red)', marginBottom: '0.5rem' }}>
                Missing Job Requirements ({tc.missing_skills?.length || 0})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {tc.missing_skills?.map((s, i) => (
                  <span key={i} className="item-badge" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.2)' }}>{s}</span>
                ))}
                {(!tc.missing_skills || tc.missing_skills.length === 0) && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None.</span>}
              </div>
            </div>

            {/* Additional Candidate Skills */}
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>
                Unutilized Candidate Skills ({tc.additional_skills?.length || 0})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {tc.additional_skills?.map((s, i) => (
                  <span key={i} className="item-badge" style={{ background: 'rgba(6, 182, 212, 0.1)', color: '#67e8f9', border: '1px solid rgba(6, 182, 212, 0.2)' }}>{s}</span>
                ))}
                {(!tc.additional_skills || tc.additional_skills.length === 0) && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None.</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Tailored Career recommendations */}
        {tc.recommendations?.length > 0 && (
          <div className="card" style={{marginTop: '2rem'}}>
            <h2 className="card-title" style={{color: 'var(--accent-yellow)', borderBottomColor: 'rgba(245, 158, 11, 0.2)'}}>
              <Shield size={20} className="text-yellow" /> Career Guidance & Recommended Resources
            </h2>
            <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
              {tc.recommendations.map((rec, idx) => (
                <div key={idx} className="recommendation-item">
                  <CheckCircle size={16} className="text-green rec-icon" />
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderActiveTabContent = () => {
    switch (activeTab) {
      case 'resume': return renderResumeTab();
      case 'profile': return renderProfileTab();
      case 'jd': return renderJdTab();
      case 'check': return renderEvaluationTab();
      case 'match': return renderSkillMatchTab();
      default: return renderResumeTab();
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="logo-container">
          <Layers size={36} className="logo-icon" />
          <h1 className="app-title">TalentCheck Dashboard</h1>
        </div>
        <p className="app-subtitle">Bridge the Gaps Between Skills and Enterprise Technical Standards</p>
      </header>

      {/* Target company evaluation selection bar */}
      <div className="company-card" style={{marginBottom: '2rem'}}>
        <div className="selector-grid">
          <div className="form-group" style={{justifyContent: 'center'}}>
            <label style={{fontSize: '1rem', color: 'var(--text-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
              <Compass size={18} className="text-green" /> Target Company Benchmarks (Talent Check)
            </label>
            <p style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>
              Select which enterprise skillset standards to check candidate profiles against in Phase 4.
            </p>
          </div>
          <div className="form-group">
            <select 
              value={selectedCompany}
              onChange={e => setSelectedCompany(e.target.value)}
              style={{padding: '0.9rem', fontSize: '1rem'}}
            >
              {companies.map(comp => (
                <option key={comp.name} value={comp.name}>{comp.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Error Alert Display */}
      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid var(--accent-red)',
          color: 'var(--accent-red)',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '2rem',
          fontSize: '0.95rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <Zap size={16} />
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Tabs navigation */}
      <div className="tabs-header">
        <button className={`tab-btn ${activeTab === 'resume' ? 'active' : ''}`} onClick={() => setActiveTab('resume')}>
          <Upload size={18} /> 1. Resume Intelligence
        </button>
        <button className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}>
          <User size={18} /> 2. Profile Builder
        </button>
        <button className={`tab-btn ${activeTab === 'jd' ? 'active' : ''}`} onClick={() => setActiveTab('jd')}>
          <FileText size={18} /> 3. JD Analytics
        </button>
        <button className={`tab-btn ${activeTab === 'check' ? 'active' : ''}`} onClick={() => setActiveTab('check')}>
          <Zap size={18} /> 4. Talent Check
        </button>
        <button className={`tab-btn ${activeTab === 'match' ? 'active' : ''}`} onClick={() => setActiveTab('match')}>
          <FileCode size={18} /> 5. Skill Matching
        </button>
      </div>

      {/* Tab Panels */}
      {renderActiveTabContent()}

      {/* Loader Overlays */}
      {(loading || matchLoading) && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(10, 11, 16, 0.8)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem'
        }}>
          <RefreshCw size={48} className="text-green animate-spin" style={{animation: 'spin 1.5s linear infinite'}} />
          <p style={{fontWeight: 600, fontSize: '1.1rem'}}>{loading ? "Evaluating candidate skills against benchmarks..." : "Calculating job description skills mapping..."}</p>
          <style>{`
            @keyframes spin {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
            .animate-spin {
              animation: spin 1.5s linear infinite;
            }
          `}</style>
        </div>
      )}
    </div>
  );
}

export default App;
