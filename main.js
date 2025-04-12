const app = new Vue({
  el: '#app',
  data: {
    isLoading: false,
    uploadedImage: null,
    extractedObjects: [],
    backgroundType: 'transparent',
    customColor: '#ffffff',
    selectedObjects: []
  },
  methods: {
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      
      // 画像ファイルかどうかの検証
      if (!file.type.match('image.*')) {
        alert('画像ファイルを選択してください');
        return;
      }
      
      this.uploadedImage = file;
      this.uploadImage();
    },
    
    handleDragOver(event) {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
    },
    
    handleDrop(event) {
      event.preventDefault();
      const file = event.dataTransfer.files[0];
      if (!file) return;
      
      if (!file.type.match('image.*')) {
        alert('画像ファイルを選択してください');
        return;
      }
      
      this.uploadedImage = file;
      this.uploadImage();
    },
    
    uploadImage() {
      if (!this.uploadedImage) return;
      
      this.isLoading = true;
      const formData = new FormData();
      formData.append('image', this.uploadedImage);
      
      // APIリクエスト
      fetch('/api/extract', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        this.extractedObjects = data.objects;
        this.isLoading = false;
      })
      .catch(error => {
        console.error('Error:', error);
        this.isLoading = false;
      });
    },
    
    downloadObject(objId) {
      const url = `/api/download/${objId}?bg=${this.backgroundType}`;
      const fullUrl = this.backgroundType === 'custom' 
        ? `${url}&color=${encodeURIComponent(this.customColor)}`
        : url;
      
      // ダウンロードを開始
      window.location.href = fullUrl;
    },
    
    downloadZip() {
      const objIds = this.selectedObjects.length > 0 
        ? this.selectedObjects 
        : this.extractedObjects.map(obj => obj.id);
      
      fetch('/api/download/zip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ids: objIds,
          bg: this.backgroundType,
          color: this.customColor
        })
      })
      .then(response => response.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'objects.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      })
      .catch(error => console.error('Error:', error));
    },
    
    toggleObjectSelection(objId) {
      const index = this.selectedObjects.indexOf(objId);
      if (index > -1) {
        this.selectedObjects.splice(index, 1);
      } else {
        this.selectedObjects.push(objId);
      }
    },
    
    selectAllObjects() {
      this.selectedObjects = this.extractedObjects.map(obj => obj.id);
    },
    
    deselectAllObjects() {
      this.selectedObjects = [];
    }
  }
});
