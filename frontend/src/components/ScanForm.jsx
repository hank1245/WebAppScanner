import React, { useState } from "react";
import DictionaryEditor from "./DictionaryEditor";

const ScanForm = ({ onScan }) => {
  const [targetUrlsInput, setTargetUrlsInput] = useState("");
  const [mode, setMode] = useState("normal");
  const [exclusions, setExclusions] = useState("");
  const [maxDepth, setMaxDepth] = useState(2);
  const [respectRobotsTxt, setRespectRobotsTxt] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const [dictionaryConfig, setDictionaryConfig] = useState({
    operations: [],
    useDefault: true,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!targetUrlsInput.trim()) {
      alert("타겟 URL 또는 IP 목록을 입력하세요.");
      return;
    }
    const targetList = targetUrlsInput
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item);

    if (targetList.length === 0) {
      alert("유효한 타겟 URL 또는 IP를 입력하세요.");
      return;
    }

    const exclusionList = exclusions
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item);

    onScan(
      targetList,
      mode,
      exclusionList,
      parseInt(maxDepth, 10),
      respectRobotsTxt,
      dictionaryConfig.operations,
      dictionaryConfig.useDefault
    );
  };

  const toggleHelp = () => {
    setShowHelp(!showHelp);
  };

  const handleDictionaryChange = (config) => {
    setDictionaryConfig(config);
  };

  return (
    <>
      {showHelp && (
        <div className="help-overlay">
          <div className="help-content">
            <h3>스캔 도움말</h3>
            <button className="help-close" onClick={toggleHelp}>
              ×
            </button>
            <div className="help-section">
              <h4>타겟 URL</h4>
              <p>
                스캔할 대상 URL을 한 줄에 하나씩 입력합니다. (예:
                http://example.com)
              </p>
            </div>
            <div className="help-section">
              <h4>모드</h4>
              <p>
                <strong>Normal:</strong> 일반 웹사이트 스캔
              </p>
              <p>
                <strong>Darkweb:</strong> .onion 도메인 스캔을 위해 Tor 프록시
                사용
              </p>
            </div>
            <div className="help-section">
              <h4>최대 깊이</h4>
              <p>
                웹사이트 내부 링크를 재귀적으로 탐색할 최대 깊이를 설정합니다.
                높은 값은 스캔 시간이 길어집니다.
              </p>
            </div>
            <div className="help-section">
              <h4>robots.txt 규칙 준수</h4>
              <p>
                웹사이트의 robots.txt 파일에 명시된 접근 제한 규칙을 따를지
                설정합니다.
              </p>
            </div>
            <div className="help-section">
              <h4>제외 목록</h4>
              <p>스캔에서 제외할 도메인이나 URL을 한 줄에 하나씩 입력합니다.</p>
            </div>
            <div className="help-section">
              <h4>딕셔너리 설정</h4>
              <p>
                스캔할 디렉토리 목록을 편집합니다. 기본 딕셔너리를 사용하거나,
                사용자 정의 항목을 추가/제거할 수 있습니다.
              </p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="scan-form">
        <div className="form-header">
          <button type="button" className="help-button" onClick={toggleHelp}>
            도움말
          </button>
        </div>

        <div className="form-group">
          <label htmlFor="targetUrls">
            <span className="form-label">타겟 URL 목록</span>
            <span className="form-hint">한 줄에 하나씩 입력</span>
          </label>
          <textarea
            id="targetUrls"
            placeholder="예: http://example.com"
            value={targetUrlsInput}
            onChange={(e) => setTargetUrlsInput(e.target.value)}
            rows="3"
            className="form-control"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="scanMode">
              <span className="form-label">스캔 모드</span>
            </label>
            <select
              id="scanMode"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="form-control"
            >
              <option value="normal">Normal</option>
              <option value="darkweb">Darkweb (.onion)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="maxDepth">
              <span className="form-label">최대 크롤링 깊이</span>
            </label>
            <input
              id="maxDepth"
              type="number"
              value={maxDepth}
              onChange={(e) => setMaxDepth(e.target.value)}
              min="0"
              max="5"
              className="form-control"
            />
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={respectRobotsTxt}
                onChange={(e) => setRespectRobotsTxt(e.target.checked)}
                className="form-checkbox"
              />
              <span>robots.txt 규칙 준수</span>
            </label>
          </div>
        </div>

        <div className="form-group dictionary-section">
          <DictionaryEditor onChange={handleDictionaryChange} />
        </div>

        <div className="form-group">
          <label htmlFor="exclusions">
            <span className="form-label">제외할 도메인 또는 URL 목록</span>
            <span className="form-hint">한 줄에 하나씩 입력</span>
          </label>
          <textarea
            id="exclusions"
            placeholder="예: admin.example.com"
            value={exclusions}
            onChange={(e) => setExclusions(e.target.value)}
            rows="2"
            className="form-control"
          />
        </div>

        <button type="submit" className="btn btn-primary scan-button">
          <span className="icon">🔍</span> 스캔 시작
        </button>
      </form>
    </>
  );
};

export default ScanForm;
