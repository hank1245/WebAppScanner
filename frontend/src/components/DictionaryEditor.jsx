import React, { useState, useEffect } from "react";
import { getDefaultDictionary } from "../api";

const DictionaryEditor = ({ onChange }) => {
  const [dictionaryItems, setDictionaryItems] = useState([]);
  const [newItem, setNewItem] = useState("");
  const [useDefaultDict, setUseDefaultDict] = useState(true);
  const [showAll, setShowAll] = useState(false);

  // 컴포넌트 마운트 시 기본 딕셔너리 로드
  useEffect(() => {
    if (useDefaultDict) {
      setDictionaryItems(getDefaultDictionary());
    }
  }, [useDefaultDict]);

  // 항목 추가
  const handleAddItem = () => {
    if (newItem.trim()) {
      // 경로에 / 추가되었는지 확인
      const formattedItem = newItem.trim().endsWith("/")
        ? newItem.trim()
        : `${newItem.trim()}/`;

      if (!dictionaryItems.includes(formattedItem)) {
        const updatedItems = [...dictionaryItems, formattedItem];
        setDictionaryItems(updatedItems);

        // 부모 컴포넌트에 변경사항 알림
        const addOperation = {
          type: "add",
          paths: [formattedItem],
        };

        onChange({
          operations: [addOperation],
          useDefault: useDefaultDict,
        });

        setNewItem("");
      } else {
        alert("이미 목록에 존재하는 항목입니다.");
      }
    }
  };

  // 항목 제거
  const handleRemoveItem = (item) => {
    const updatedItems = dictionaryItems.filter((i) => i !== item);
    setDictionaryItems(updatedItems);

    // 부모 컴포넌트에 변경사항 알림
    const removeOperation = {
      type: "remove",
      paths: [item],
    };

    onChange({
      operations: [removeOperation],
      useDefault: useDefaultDict,
    });
  };

  // 기본 딕셔너리 사용 여부 토글
  const handleDefaultToggle = () => {
    const newValue = !useDefaultDict;
    setUseDefaultDict(newValue);

    if (newValue) {
      // 기본 딕셔너리 사용으로 전환
      setDictionaryItems(getDefaultDictionary());
    } else {
      // 기본 딕셔너리 사용 중지, 사용자 정의 목록만 사용
      setDictionaryItems([]);
    }

    // 부모 컴포넌트에 변경사항 알림
    onChange({
      operations: [],
      useDefault: newValue,
    });
  };

  // 표시할 항목 수 계산
  const visibleItems = showAll ? dictionaryItems : dictionaryItems.slice(0, 10);

  return (
    <div className="dictionary-editor">
      <h3 className="form-label">딕셔너리 설정</h3>
      <p className="form-hint">스캔할 디렉토리 경로 목록을 관리합니다.</p>

      <div className="form-group checkbox-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={useDefaultDict}
            onChange={handleDefaultToggle}
            className="form-checkbox"
          />
          <span>기본 딕셔너리 사용 (권장)</span>
        </label>
      </div>

      <div className="dictionary-input-group">
        <input
          type="text"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          placeholder="추가할 디렉토리 경로 (예: admin/)"
          className="form-control"
          style={{ flex: 1 }}
        />
        <button
          type="button"
          onClick={handleAddItem}
          className="btn btn-secondary"
          disabled={!newItem.trim()}
        >
          추가
        </button>
      </div>

      <div className="dictionary-list">
        <p className="form-hint">
          현재 딕셔너리 항목: {dictionaryItems.length}개
          {dictionaryItems.length > 10 && !showAll && (
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="btn-link"
            >
              모두 보기
            </button>
          )}
          {showAll && (
            <button
              type="button"
              onClick={() => setShowAll(false)}
              className="btn-link"
            >
              접기
            </button>
          )}
        </p>

        <div className="dictionary-items">
          {visibleItems.length > 0 ? (
            visibleItems.map((item, index) => (
              <div key={index} className="dictionary-item">
                <span>{item}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveItem(item)}
                  className="btn-close"
                  aria-label="Remove"
                >
                  ×
                </button>
              </div>
            ))
          ) : (
            <p className="empty-message">딕셔너리 항목이 비어있습니다.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default DictionaryEditor;
