from datetime import datetime, timezone
from urllib.parse import urlsplit
import sqlalchemy as sa
from flask import render_template, flash, redirect, url_for, request, g
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import app, db
from app.forms import (LoginForm, RegistrationForm, EditProfileForm, EmptyForm,
                       PostForm, ResetPasswordRequestForm, ResetPasswordForm)
from app.models import User, Post
from app.email import send_password_reset_email
from app.translate import translate


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        try:
            lang_detected = detect(form.post.data)
        except LangDetectException:
            lang_detected = ''
        new_post = Post(body=form.post.data, author=current_user,
                        language=lang_detected)
        db.session.add(new_post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    page_num = request.args.get('page', 1, type=int)
    post_query = current_user.following_posts()
    paginated = db.paginate(post_query, page=page_num,
                            per_page=app.config['POSTS_PER_PAGE'],
                            error_out=False)
    next_url = url_for('index', page=paginated.next_num) \
        if paginated.has_next else None
    prev_url = url_for('index', page=paginated.prev_num) \
        if paginated.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=paginated.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page_num = request.args.get('page', 1, type=int)
    post_query = sa.select(Post).order_by(Post.timestamp.desc())
    paginated = db.paginate(post_query, page=page_num,
                            per_page=app.config['POSTS_PER_PAGE'],
                            error_out=False)
    next_url = url_for('explore', page=paginated.next_num) \
        if paginated.has_next else None
    prev_url = url_for('explore', page=paginated.prev_num) \
        if paginated.has_prev else None
    return render_template('index.html', title=_('Discover'), posts=paginated.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        usr = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if usr is None or not usr.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(usr, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_usr = User(username=form.username.data, email=form.email.data)
        new_usr.set_password(form.password.data)
        db.session.add(new_usr)
        db.session.commit()
        flash(_('Welcome! Your account has been created.'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    usr = db.first_or_404(sa.select(User).where(User.username == username))
    page_num = request.args.get('page', 1, type=int)
    post_query = usr.posts.select().order_by(Post.timestamp.desc())
    paginated = db.paginate(post_query, page=page_num,
                            per_page=app.config['POSTS_PER_PAGE'],
                            error_out=False)
    next_url = url_for('user', username=usr.username, page=paginated.next_num) \
        if paginated.has_next else None
    prev_url = url_for('user', username=usr.username, page=paginated.prev_num) \
        if paginated.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=usr, posts=paginated.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        usr = db.session.scalar(
            sa.select(User).where(User.username == username))
        if usr is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('index'))
        if usr == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('user', username=username))
        current_user.follow(usr)
        db.session.commit()
        flash(_('You are now following %(username)s!', username=username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        usr = db.session.scalar(
            sa.select(User).where(User.username == username))
        if usr is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('index'))
        if usr == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('user', username=username))
        current_user.unfollow(usr)
        db.session.commit()
        flash(_('You have unfollowed %(username)s.', username=username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    payload = request.get_json()
    result = translate(payload['text'], payload['source_language'],
                       payload['dest_language'])
    return {'text': result}


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        usr = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if usr:
            send_password_reset_email(usr)
        flash(_('Check your email for password reset instructions.'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    usr = User.verify_reset_password_token(token)
    if not usr:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        usr.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset successfully.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
