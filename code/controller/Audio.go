package controller

import (
	"encoding/json"
	"simUI/code/modules"
	"simUI/code/utils"
	"simUI/code/utils/go-sciter"
)

/**
 * 定义view用function
 **/

func AudioController() {

	//读取音频文件列表
	utils.Window.DefineFunction("GetAudio", func(args ...*sciter.Value) *sciter.Value {
		id := uint64(utils.ToInt(args[0].String()))
		volist,err := modules.GetAudioList(id)
		if err != nil {
			utils.WriteLog(err.Error())
			return utils.ErrorMsg(err.Error())
		}
		jsonInfo, _ := json.Marshal(volist)
		return sciter.NewValue(string(jsonInfo))
	})

	//上传文件
	utils.Window.DefineFunction("UploadAudioFile", func(args ...*sciter.Value) *sciter.Value {
		id := uint64(utils.ToInt(args[0].String()))
		name := args[1].String()
		p := args[2].String()

		relPath, err := modules.UploadAudioFile(id, name, p)
		if err != nil {
			utils.WriteLog(err.Error())
			return utils.ErrorMsg(err.Error())
		}

		return sciter.NewValue(relPath)
	})

	//更新配置
	utils.Window.DefineFunction("UpdateAudio", func(args ...*sciter.Value) *sciter.Value {
		id := uint64(utils.ToInt(args[0].String()))
		data := args[1].String()
		if err := modules.UpdateAudio(id, data); err != nil {
			utils.WriteLog(err.Error())
			return utils.ErrorMsg(err.Error())
		}
		return sciter.NullValue()
	})

	//打开攻略文件
	utils.Window.DefineFunction("OpenAudio", func(args ...*sciter.Value) *sciter.Value {
		p := args[0].String()
		if err := modules.OpenAudioFile(p); err != nil {
			utils.WriteLog(err.Error())
			return utils.ErrorMsg(err.Error())
		}
		return sciter.NullValue()
	})

}
