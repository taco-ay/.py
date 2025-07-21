import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
manager = DB_Manager(DATABASE)

@bot.event
async def on_ready():
    print(f'Bot hazır! {bot.user} olarak giriş yapıldı.')

@bot.command(name='start')
async def start_command(ctx):
    await ctx.send("Merhaba! Ben bir proje yöneticisi botuyum.\nProjelerinizi ve onlara dair tüm bilgileri saklamanıza yardımcı olacağım! =)")
    await info(ctx)

@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Kullanabileceğiniz komutlar şunlardır:

!new_project - yeni bir proje eklemek
!projects - tüm projelerinizi listelemek
!update_projects - proje verilerini güncellemek
!skills - belirli bir projeye beceri eklemek
!delete - bir projeyi silmek

Ayrıca, proje adını yazarak projeyle ilgili tüm bilgilere göz atabilirsiniz!""")

# ✅ YENİ PROJE EKLEME
@bot.command(name='new_project')
async def new_project(ctx):
    await ctx.send("Lütfen projenin adını girin!")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    name = await bot.wait_for('message', check=check)

    await ctx.send("Projenin açıklamasını girin (boş bırakabilirsiniz).")
    desc_msg = await bot.wait_for('message', check=check)
    description = desc_msg.content if desc_msg.content else ""

    await ctx.send("Lütfen projeye ait bağlantıyı gönderin!")
    link = await bot.wait_for('message', check=check)

    statuses = [x[0] for x in manager.get_statuses()]
    await ctx.send("Lütfen projenin mevcut durumunu girin!")
    await ctx.send("\n".join(statuses))

    status = await bot.wait_for('message', check=check)
    if status.content not in statuses:
        await ctx.send("Seçtiğiniz durum listede bulunmuyor. Lütfen tekrar deneyin!")
        return

    await ctx.send("Projeye ait ekran görüntüsü bağlantısını gönderin (isterseniz boş bırakabilirsiniz).")
    screenshot_msg = await bot.wait_for('message', check=check)
    screenshot = screenshot_msg.content if screenshot_msg.content else None

    manager.insert_project(
        ctx.author.id,
        name.content,
        description,
        link.content,
        status.content,
        screenshot
    )
    await ctx.send("✅ Proje başarıyla kaydedildi!")

# ✅ TÜM PROJELERİ LİSTELEME
@bot.command(name='projects')
async def get_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([
            f"📌 **{x[2]}**\n📝 Açıklama: {x[3] if x[3] else 'Yok'}\n🔗 Link: {x[4]}\n🖼 Screenshot: {x[6] if x[6] else 'Yok'}\n"
            for x in projects
        ])
        await ctx.send(text)
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# ✅ PROJEYE BECERİ EKLEME
@bot.command(name='skills')
async def skills(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects_list = [x[2] for x in projects]
        await ctx.send('Bir beceri eklemek istediğiniz projeyi seçin')
        await ctx.send("\n".join(projects_list))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects_list:
            await ctx.send('Bu projeye sahip değilsiniz, lütfen tekrar deneyin!')
            return

        skills_list = [x[1] for x in manager.get_skills()]
        await ctx.send('Bir beceri seçin')
        await ctx.send("\n".join(skills_list))

        skill = await bot.wait_for('message', check=check)
        if skill.content not in skills_list:
            await ctx.send('Görünüşe göre seçtiğiniz beceri listede yok! Lütfen tekrar deneyin!')
            return

        manager.insert_skill(user_id, project_name.content, skill.content)
        await ctx.send(f'✅ {skill.content} becerisi {project_name.content} projesine eklendi!')
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# ✅ PROJE SİLME
@bot.command(name='delete')
async def delete_project(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects_list = [x[2] for x in projects]
        await ctx.send("Silmek istediğiniz projeyi seçin")
        await ctx.send("\n".join(projects_list))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects_list:
            await ctx.send('Bu projeye sahip değilsiniz, lütfen tekrar deneyin!')
            return

        project_id = manager.get_project_id(project_name.content, user_id)
        manager.delete_project(user_id, project_id)
        await ctx.send(f'❌ {project_name.content} projesi veri tabanından silindi!')
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# ✅ PROJE GÜNCELLEME
@bot.command(name='update_projects')
async def update_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects_list = [x[2] for x in projects]
        await ctx.send("Güncellemek istediğiniz projeyi seçin")
        await ctx.send("\n".join(projects_list))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name_msg = await bot.wait_for('message', check=check)
        if project_name_msg.content not in projects_list:
            await ctx.send("Bir hata oldu! Lütfen güncellemek istediğiniz projeyi tekrar seçin:")
            return

        project_id = manager.get_project_id(project_name_msg.content, user_id)

        await ctx.send("Projede neyi değiştirmek istersiniz?")
        attributes = {
            'Proje adı': 'project_name',
            'Açıklama': 'description',
            'Proje bağlantısı': 'url',
            'Proje durumu': 'status_id',
            'Screenshot': 'screenshot'
        }
        await ctx.send("\n".join(attributes.keys()))

        attribute_msg = await bot.wait_for('message', check=check)
        if attribute_msg.content not in attributes:
            await ctx.send("Hata oluştu! Lütfen tekrar deneyin!")
            return

        chosen_attribute = attributes[attribute_msg.content]

        if chosen_attribute == 'status_id':
            statuses = [x[0] for x in manager.get_statuses()]
            await ctx.send("Projeniz için yeni bir durum seçin")
            await ctx.send("\n".join(statuses))
            update_info_msg = await bot.wait_for('message', check=check)
            if update_info_msg.content not in statuses:
                await ctx.send("Yanlış durum seçildi, lütfen tekrar deneyin!")
                return
            update_value = manager.get_status_id(update_info_msg.content)
        else:
            await ctx.send(f"{attribute_msg.content} için yeni bir değer girin")
            update_info_msg = await bot.wait_for('message', check=check)
            update_value = update_info_msg.content

        manager.update_projects(chosen_attribute, update_value, project_id)
        await ctx.send("✅ Tüm işlemler tamamlandı! Proje güncellendi!")
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

bot.run(TOKEN)
