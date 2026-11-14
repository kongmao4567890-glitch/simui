// dbschema 把数据库补齐到当前代码使用的表结构，并可清空开发数据，生成可直接发布的 data.db。
//
// 用法：go run ./tools/dbschema -db path/to/data.db [-clean] [-theme Book] [-lang 简体中文]
//
// 仓库自带的 data.dll 是早期开发库，缺少 rom_name / link_file / pid 等列。
// 本工具按 db 包中的结构体逐列比对，缺少的表用 gorm 建立，缺少的列用
// "NOT NULL DEFAULT ..." 方式补齐，保证与程序的读写语句一致。
package main

import (
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"reflect"
	"strings"

	"github.com/jinzhu/gorm"
	_ "github.com/mattn/go-sqlite3"

	"simUI/db"
)

type tabler interface{ TableName() string }

func main() {
	path := flag.String("db", "data.db", "数据库文件")
	clean := flag.Bool("clean", false, "清空平台、游戏、模拟器等开发数据")
	theme := flag.String("theme", "", "设置默认主题，如 Book")
	lang := flag.String("lang", "", "设置默认语言，如 简体中文")
	flag.Parse()

	conn, err := gorm.Open("sqlite3", *path)
	if err != nil {
		fail(err)
	}
	defer conn.Close()
	raw := conn.DB()

	models := []tabler{
		&db.Config{}, &db.Filter{}, &db.Menu{}, &db.Platform{}, &db.Rom{},
		&db.RombaseAlias{}, &db.RombaseEnum{}, &db.Shortcut{}, &db.Simulator{}, &db.Thumbs{},
	}

	for _, m := range models {
		table := m.TableName()
		cols := existingColumns(raw, table)
		if len(cols) == 0 {
			if err := conn.AutoMigrate(m).Error; err != nil {
				fail(err)
			}
			fmt.Println("create table", table)
			continue
		}
		t := reflect.TypeOf(m).Elem()
		for i := 0; i < t.NumField(); i++ {
			f := t.Field(i)
			if !f.IsExported() || f.Tag.Get("gorm") == "-" {
				continue
			}
			col := gorm.ToColumnName(f.Name)
			if cols[col] {
				continue
			}
			typ, def := sqlType(f.Type.Kind())
			if typ == "" {
				continue
			}
			stmt := fmt.Sprintf(`ALTER TABLE %q ADD COLUMN %q %s NOT NULL DEFAULT %s`, table, col, typ, def)
			if _, err := raw.Exec(stmt); err != nil {
				fail(fmt.Errorf("%s: %w", stmt, err))
			}
			fmt.Println(stmt)
		}
	}

	// 补齐当前代码需要的配置项（早期数据库缺少或格式不对的会导致界面颜色、边栏显示异常）
	ensureConfig(raw, "Colors", `{"ThemeColor":"rgb(17, 17, 17)","ThemeTextColor":"#FFFFFF","ThemeBrandColor":"#1976D2","ThemeBrandTextColor":"#FFFFFF"}`, "主题颜色配置", true)
	ensureConfig(raw, "FrameShowDefault", `{"LogoShow":true,"PlatformShow":true,"MenuShow":true,"RightShow":true}`, "窗体框架显示状态", true)
	ensureConfig(raw, "SplashScreen", `{"Src":"","Size":"","Time":0}`, "开屏画面参数", true)
	ensureConfig(raw, "SoftName", `{"Name":"SimUI","SubName":"","Image":"","HideText":0}`, "软件名称", true)
	ensureConfig(raw, "ThumbOrders", `[]`, "展示图排序", true)
	ensureConfig(raw, "Menu", `["",0]`, "当前选定菜单", true)
	ensureConfig(raw, "WindowZoom", "1", "窗口缩放比例", false)
	ensureConfig(raw, "VideoVolume", "0.5", "视频默认音量", false)
	ensureConfig(raw, "AdminRunGame", "0", "以管理员身份启动游戏", false)
	ensureConfig(raw, "GameMultiOpen", "0", "是否允许模拟器游戏多开", false)
	ensureConfig(raw, "VersionNo", "", "当前版本号或已跳过的版本号", false)
	mustExec(raw, `DELETE FROM config WHERE name = 'BarShowStatus'`) // 已被 FrameShowDefault 取代

	// 升级 SQL 已由本工具覆盖，记录为全部执行过，避免启动时重复执行
	n := len(db.DbUpdateSqlList(""))
	upsert(raw, "SqlUpdateNum", fmt.Sprint(n), "sql升级条数")

	if *clean {
		for _, t := range []string{"rom", "platform", "simulator", "menu", "filter", "shortcut", "rombase_alias", "thumbs"} {
			if len(existingColumns(raw, t)) > 0 {
				mustExec(raw, "DELETE FROM "+t)
			}
		}
		for _, t := range []string{"rom_subgame", "rom_setting"} { // 早期遗留的表
			mustExec(raw, "DROP TABLE IF EXISTS "+t)
		}
		upsert(raw, "Platform", "0", "当前选定平台")
		upsert(raw, "Menu", `["",0]`, "当前选定菜单")
		upsert(raw, "SoftName", `{"Name":"SimUI","SubName":"","Image":""}`, "SimUI")
		upsert(raw, "EnableUpgrade", "0", "是否启用更新")
		upsert(raw, "WindowState", "0", "窗体状态")
		upsert(raw, "WindowWidth", "1280", "窗体宽度")
		upsert(raw, "WindowHeight", "800", "窗体高度")
		mustExec(raw, "UPDATE sqlite_sequence SET seq = 0")
	}
	if *theme != "" {
		upsert(raw, "Theme", *theme, "主题")
	}
	if *lang != "" {
		// 命令行在部分 Windows 终端下传递中文可能乱码，提供英文别名
		aliases := map[string]string{"zh-CN": "简体中文", "zh": "简体中文", "en": "English"}
		if v, ok := aliases[*lang]; ok {
			*lang = v
		}
		upsert(raw, "Lang", *lang, "语言")
	}
	mustExec(raw, "VACUUM")
	fmt.Println("ok:", *path)
}

// ensureConfig 配置项不存在时写入默认值；mustJSON 为 true 时，现有值不是合法 JSON 也会被替换
func ensureConfig(raw *sql.DB, name, def, desc string, mustJSON bool) {
	var cur sql.NullString
	err := raw.QueryRow(`SELECT data FROM config WHERE name = ?`, name).Scan(&cur)
	if err == nil {
		if !mustJSON || (cur.String != "" && json.Valid([]byte(cur.String))) {
			return
		}
	}
	upsert(raw, name, def, desc)
}

func existingColumns(raw *sql.DB, table string) map[string]bool {
	rows, err := raw.Query(fmt.Sprintf("PRAGMA table_info(%q)", table))
	if err != nil {
		fail(err)
	}
	defer rows.Close()
	cols := map[string]bool{}
	for rows.Next() {
		var cid, notnull, pk int
		var name, typ string
		var dflt sql.NullString
		if err := rows.Scan(&cid, &name, &typ, &notnull, &dflt, &pk); err != nil {
			fail(err)
		}
		cols[strings.ToLower(name)] = true
	}
	return cols
}

func sqlType(k reflect.Kind) (string, string) {
	switch k {
	case reflect.String:
		return "TEXT", "''"
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64,
		reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Bool:
		return "INTEGER", "0"
	case reflect.Float32, reflect.Float64:
		return "REAL", "0"
	}
	return "", ""
}

func upsert(raw *sql.DB, name, data, desc string) {
	res, err := raw.Exec(`UPDATE config SET data = ? WHERE name = ?`, data, name)
	if err != nil {
		fail(err)
	}
	if n, _ := res.RowsAffected(); n == 0 {
		mustExec(raw, `INSERT INTO config (name, data, "desc") VALUES (?, ?, ?)`, name, data, desc)
	}
}

func mustExec(raw *sql.DB, q string, args ...any) {
	if _, err := raw.Exec(q, args...); err != nil {
		fail(fmt.Errorf("%s: %w", q, err))
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, "dbschema:", err)
	os.Exit(1)
}
