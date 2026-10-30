import { useEffect, useState } from 'react'
import { api, type Branch, type User } from '../api'
import { EmptyState, Field, Modal, Notice, PageHeader, StatusPill, Tabs } from '../components/Ui'

type AdminTab = 'usuarios' | 'sucursales'

const emptyUser = { name: '', email: '', password: '', role: 'EMPLEADO', branch_id: '' }
const emptyBranch = { name: '', address: '' }

export function AdminPage() {
  const [tab, setTab] = useState<AdminTab>('usuarios')
  const [users, setUsers] = useState<User[]>([])
  const [branches, setBranches] = useState<Branch[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [userModal, setUserModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [userForm, setUserForm] = useState(emptyUser)
  const [branchModal, setBranchModal] = useState(false)
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null)
  const [branchForm, setBranchForm] = useState(emptyBranch)

  const reload = async () => {
    const [userList, branchList] = await Promise.all([api.users(), api.branches()])
    setUsers(userList)
    setBranches(branchList)
  }

  useEffect(() => { reload().catch(err => setError(err.message)) }, [])

  const openNewUser = () => {
    setEditingUser(null)
    setUserForm({ ...emptyUser, branch_id: String(branches[0]?.id ?? '') })
    setError('')
    setUserModal(true)
  }

  const openEditUser = (user: User) => {
    setEditingUser(user)
    setUserForm({ name: user.name, email: user.email, password: '', role: user.role, branch_id: String(user.branch_id) })
    setError('')
    setUserModal(true)
  }

  const saveUser = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      if (editingUser) {
        const payload: Record<string, unknown> = {
          name: userForm.name,
          email: userForm.email,
          role: userForm.role,
          branch_id: Number(userForm.branch_id),
        }
        if (userForm.password) payload.password = userForm.password
        await api.updateUser(editingUser.id, payload)
        setSuccess(`Usuario ${userForm.name} actualizado.`)
      } else {
        await api.createUser({
          name: userForm.name,
          email: userForm.email,
          password: userForm.password,
          role: userForm.role,
          branch_id: Number(userForm.branch_id),
        })
        setSuccess(`Usuario ${userForm.name} creado.`)
      }
      setUserModal(false)
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el usuario')
    }
  }

  const toggleUser = async (user: User) => {
    setError('')
    try {
      await api.updateUser(user.id, { active: !user.active })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar el usuario')
    }
  }

  const openNewBranch = () => {
    setEditingBranch(null)
    setBranchForm(emptyBranch)
    setError('')
    setBranchModal(true)
  }

  const openEditBranch = (branch: Branch) => {
    setEditingBranch(branch)
    setBranchForm({ name: branch.name, address: branch.address ?? '' })
    setError('')
    setBranchModal(true)
  }

  const saveBranch = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      if (editingBranch) {
        await api.updateBranch(editingBranch.id, { name: branchForm.name, address: branchForm.address || null })
        setSuccess(`Sucursal ${branchForm.name} actualizada.`)
      } else {
        await api.createBranch({ name: branchForm.name, address: branchForm.address || undefined })
        setSuccess(`Sucursal ${branchForm.name} creada.`)
      }
      setBranchModal(false)
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la sucursal')
    }
  }

  const toggleBranch = async (branch: Branch) => {
    setError('')
    try {
      await api.updateBranch(branch.id, { active: !branch.active })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar la sucursal')
    }
  }

  const branchName = (id: number) => branches.find(branch => branch.id === id)?.name ?? `#${id}`

  return <>
    <PageHeader eyebrow="ADMINISTRACIÓN" title="Usuarios y sucursales" description="Gestioná el acceso del equipo y la estructura de la farmacia." />
    <Tabs value={tab} onChange={setTab} options={[{ value: 'usuarios', label: 'Usuarios' }, { value: 'sucursales', label: 'Sucursales' }]} />
    {error && <Notice>{error}</Notice>}
    {success && <Notice tone="success">{success}</Notice>}

    {tab === 'usuarios' ? <div className="panel table-panel">
      <div className="table-heading"><div><h2>Equipo</h2><span>{users.length} usuarios</span></div><button className="primary-button" onClick={openNewUser}>+ Nuevo usuario</button></div>
      {users.length === 0 ? <EmptyState title="Sin usuarios" message="Creá el primer usuario para operar el sistema." /> : <div className="table-scroll"><table>
        <thead><tr><th>Nombre</th><th>Email</th><th>Rol</th><th>Sucursal</th><th>Estado</th><th /></tr></thead>
        <tbody>{users.map(user => <tr key={user.id}>
          <td><strong>{user.name}</strong></td>
          <td className="mono">{user.email}</td>
          <td><StatusPill tone={user.role === 'ADMIN' ? 'warning' : 'neutral'}>{user.role === 'ADMIN' ? 'Administrador' : 'Empleado'}</StatusPill></td>
          <td>{branchName(user.branch_id)}</td>
          <td><StatusPill tone={user.active ? 'success' : 'danger'}>{user.active ? 'Activo' : 'Inactivo'}</StatusPill></td>
          <td><div className="inline-actions"><button className="secondary-button" onClick={() => openEditUser(user)}>Editar</button><button className="danger-button" onClick={() => toggleUser(user)}>{user.active ? 'Desactivar' : 'Activar'}</button></div></td>
        </tr>)}</tbody>
      </table></div>}
    </div> : <div className="panel table-panel">
      <div className="table-heading"><div><h2>Sucursales</h2><span>{branches.length} sucursales</span></div><button className="primary-button" onClick={openNewBranch}>+ Nueva sucursal</button></div>
      {branches.length === 0 ? <EmptyState title="Sin sucursales" message="Creá la primera sucursal para asignar usuarios." /> : <div className="table-scroll"><table>
        <thead><tr><th>Nombre</th><th>Dirección</th><th>Estado</th><th /></tr></thead>
        <tbody>{branches.map(branch => <tr key={branch.id}>
          <td><strong>{branch.name}</strong></td>
          <td>{branch.address || '—'}</td>
          <td><StatusPill tone={branch.active ? 'success' : 'danger'}>{branch.active ? 'Activa' : 'Inactiva'}</StatusPill></td>
          <td><div className="inline-actions"><button className="secondary-button" onClick={() => openEditBranch(branch)}>Editar</button><button className="danger-button" onClick={() => toggleBranch(branch)}>{branch.active ? 'Desactivar' : 'Activar'}</button></div></td>
        </tr>)}</tbody>
      </table></div>}
    </div>}

    <Modal open={userModal} title={editingUser ? 'Editar usuario' : 'Nuevo usuario'} description="Los cambios de rol impactan en los permisos de inmediato." onClose={() => setUserModal(false)}>
      <form onSubmit={saveUser}>
        <div className="form-grid">
          <Field label="Nombre"><input value={userForm.name} onChange={event => setUserForm({ ...userForm, name: event.target.value })} required /></Field>
          <Field label="Email"><input type="email" value={userForm.email} onChange={event => setUserForm({ ...userForm, email: event.target.value })} required /></Field>
          <Field label={editingUser ? 'Nueva contraseña' : 'Contraseña'} hint={editingUser ? 'Dejala vacía para conservarla.' : 'Mínimo 8 caracteres.'}>
            <input type="password" value={userForm.password} onChange={event => setUserForm({ ...userForm, password: event.target.value })} required={!editingUser} minLength={8} />
          </Field>
          <Field label="Rol"><select value={userForm.role} onChange={event => setUserForm({ ...userForm, role: event.target.value })}><option value="EMPLEADO">Empleado</option><option value="ADMIN">Administrador</option></select></Field>
          <Field label="Sucursal" hint="No podés quitarte tu propio rol de administrador."><select value={userForm.branch_id} onChange={event => setUserForm({ ...userForm, branch_id: event.target.value })} required>{branches.map(branch => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></Field>
        </div>
        <div className="form-actions"><button type="button" className="secondary-button" onClick={() => setUserModal(false)}>Cancelar</button><button className="primary-button">Guardar</button></div>
      </form>
    </Modal>

    <Modal open={branchModal} title={editingBranch ? 'Editar sucursal' : 'Nueva sucursal'} onClose={() => setBranchModal(false)}>
      <form onSubmit={saveBranch}>
        <div className="form-grid">
          <Field label="Nombre"><input value={branchForm.name} onChange={event => setBranchForm({ ...branchForm, name: event.target.value })} required /></Field>
          <Field label="Dirección"><input value={branchForm.address} onChange={event => setBranchForm({ ...branchForm, address: event.target.value })} /></Field>
        </div>
        <div className="form-actions"><button type="button" className="secondary-button" onClick={() => setBranchModal(false)}>Cancelar</button><button className="primary-button">Guardar</button></div>
      </form>
    </Modal>
  </>
}
