var app = new Vue({
  el: "#app",
  data: {
    tableData: '',
    search: '',
    dialogFormVisible: false,
    form: {
      name: '',
      ip: '',
      sshuser: '',
      sshpasswd: '',
    },
  },
  
  methods: {
    addServer(){
      
      if(this.form.name==''||this.form.ip==''||this.form.sshsuer==''||this.form.sshpasswd==''){
        this.$notify.error({
          title: '错误',
          message: '存在未填信息'
        });
        return
      }
      
      axios.post("http://127.0.0.1:8090/server/",{"name":this.form.name,"ip":this.form.ip,"sshuser":this.form.sshuser,"sshpasswd":this.form.sshpasswd})
      .then(res => {
        res = res.data.status
        if((res)==33333){
          this.$notify.error({
            title: '错误',
            message: 'ip地址格式不正确'
          });

          return
        }
        if(res==200){
          this.$notify({
            title: '添加成功',
            message: '已添加主机'
          });
          this.dialogFormVisible = false 
        }
       
      })
      .catch(err => {
        console.error(err); 
      })
    },
    handleEdit(index, row) {
      console.log(index, row);
    },
    handleDelete(index, row) {
      id = row.id
      axios.delete("http://127.0.0.1:8090/index",{"id":id})
      .then(res => {
        console.log(res)
        this.$notify({
          title: '删除成功',
          message: '已删除主机'
        });
      })
      .catch(err => {
        console.error(err); 
      })
    }
  }
})
axios.get('http://127.0.0.1:8090/server/')
  .then(function (response) {
    console.log(app.tableData = response.data.content);
  })
  .catch(function (error) {
    console.log(error);
  });